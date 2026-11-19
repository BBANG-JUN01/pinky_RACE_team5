import json
import math
from pathlib import Path
import tempfile
import unittest
from pinky_gp_navigation import track_fixture as track
from pinky_gp_navigation.scan_race import Occupancy,SIM_LIMITS
from pinky_gp_navigation.raceline import RacingProfile,optimize,trajectory,validate_path,curvature
from pinky_gp_navigation.vehicle_profile import load_profile


class RacelineTests(unittest.TestCase):
    def setUp(self):
        self.grid=Occupancy(track.WIDTH,track.HEIGHT,track.RES,track.ORIGIN,track.occupancy())
        self.points=track.centerline()
        self.profile=RacingProfile(SIM_LIMITS)

    def test_same_limits_improve_and_preserve_grid(self):
        q=optimize(self.points,self.grid,self.profile)
        self.assertLess(q['optimization']['optimized_estimated_s'],q['optimization']['baseline_estimated_s']*.95)
        self.assertEqual(q['points'][:3],self.points[:3])
        validate_path(q['points'],self.grid)

    def test_envelope_acceleration_braking_and_wheels(self):
        speed,_=trajectory(self.points,self.profile)
        for i,p in enumerate(self.points):
            j=(i+1)%len(speed);d=math.dist(p,self.points[j])
            self.assertLessEqual(speed[j]**2,speed[i]**2+2*self.profile.acceleration*d+1e-8)
            self.assertLessEqual(speed[i]**2,speed[j]**2+2*self.profile.limits.braking*d+1e-8)
            self.assertLessEqual(speed[i]*(1+abs(curvature(self.points)[i])*.0961/2),.28+1e-8)

    def test_segment_through_wall_fails_even_with_free_endpoints(self):
        with self.assertRaisesRegex(ValueError,'SEGMENT_BLOCKED'):
            validate_path([(0,0),(0,1.44),(1.32,0)],self.grid)

    def test_invalid_profile_does_not_enable_hardware(self):
        path=Path(__file__).parents[1]/'src/pinky_gp_bringup/config/racing_sim.json'
        with self.assertRaises(ValueError):load_profile(path,hardware=True)

    def test_zero_and_nonfinite_bounds_rejected(self):
        for value in (0.,float('nan'),.8):
            with self.assertRaises(ValueError):
                optimize(self.points,self.grid,self.profile,max_offset=value)
