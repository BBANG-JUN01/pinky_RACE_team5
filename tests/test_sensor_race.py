import math
import tempfile
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from pinky_gp_core.sensor_time import fresh
from pinky_gp_guard.guard_core import CommandGuard
from pinky_gp_navigation import track_fixture as track
from pinky_gp_navigation.scan_race import RaceDrive, Occupancy, scan_points
from pinky_gp_race.race_manager import RaceManager


class RaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid=Occupancy(track.WIDTH,track.HEIGHT,track.RES,track.ORIGIN,track.occupancy())

    def setUp(self):
        self.drive=RaceDrive(track.centerline(),self.grid)
        self.pose=(0.,0.,0.)

    def step(self,at=1.,v=0.,w=0.):
        return self.drive.step(self.pose,[],at,v,w)

    def test_transform_backwards_mounted_lidar(self):
        hits=scan_points([1.]*80,-math.pi,2*math.pi/79,.05,12.,(-.017,0.,math.pi))
        self.assertAlmostEqual(hits[0][0],.983)
        self.assertAlmostEqual(hits[0][1],0.)

    def test_blind_scan_full_wedge(self):
        r=[1.]*80
        r[18:44]=[float('inf')]*26
        with self.assertRaisesRegex(ValueError,'BLIND'):scan_points(r,-math.pi,2*math.pi/79,.05,12.,self.pose)

    def test_reject_bad_geometry(self):
        for seq in ([math.nan]*80,[math.inf]*80,[.01]*80,[1.]*5):
            with self.assertRaises(ValueError):scan_points(seq,-math.pi,2*math.pi/79,.05,12.,self.pose)
        with self.assertRaises(ValueError):scan_points([1.]*80,0,.001,.05,12.,self.pose)

    def test_map_footprint_and_edges(self):
        self.assertFalse(self.grid.clear((.0,.53),set()))
        self.assertFalse(self.grid.clear((-2.04,-.66),set()))
        self.assertTrue(self.grid.clear((0,0),set()))

    def test_gazebo_and_pgm_share_metric_world(self):
        with tempfile.TemporaryDirectory() as name:
            p=Path(name);track.write_track(p)
            boxes=ET.parse(p/'track.sdf').findall('.//world/model')
            self.assertEqual(len(boxes),1+len(track.WALLS))
            self.assertEqual(len((p/'map.pgm').read_bytes().split(b'\n',3)[3]),track.WIDTH*track.HEIGHT)
            self.assertNotIn('barrier',(p/'track.sdf').read_text())

    def test_stopped_candidate_must_be_renewed(self):
        g=CommandGuard(.3,.8,.35,());g.select('nav');g.stop('person')
        self.assertFalse(g.receive('nav',.2,0.,1.))
        g.stop('person',False)
        self.assertEqual(g.tick(1.)[0],0.)
        self.assertTrue(g.receive('nav',.2,0.,1.1))

    def test_source_time(self):
        for stamp in (0.,math.nan,1.1,.4):
            self.assertFalse(fresh(stamp,1.,.35))
        self.assertTrue(fresh(.8,1.,.35))

    def test_actual_start_grid(self):
        self.pose=(.34,0.,0.)
        self.assertEqual(self.step().reason,'START_OUTSIDE_GRID')

    def test_physical_jump_latched(self):
        self.step()
        self.pose=(0.,.19,0.)
        self.assertEqual(self.step(1.1).reason,'LOCALIZATION_JUMP')
        self.pose=(0.,0.,0.)
        self.assertEqual(self.step(1.2).v,0.)

    def test_no_lap_from_finish_jitter(self):
        for i in range(30):
            self.pose=(.015*(-1)**i,0.,0.)
            self.step(1.+.1*i)
        self.assertFalse(self.drive.timer.laps)

    def test_reverse_heading_and_old_sample(self):
        self.step()
        self.assertEqual(self.step().reason,'OLD_SAMPLE')
        self.pose=(0.,0.,math.pi)
        self.assertEqual(self.step(1.1).reason,'WRONG_HEADING')

    def test_penalty_requires_observed_continuous_stop(self):
        self.drive.event('PENALTY','p',1.,.5)
        self.step(1.);self.step(1.2);self.step(1.3,v=.05)
        self.assertEqual(self.step(1.5).reason,'PENALTY')
        self.assertEqual(self.step(3.).reason,'PENALTY')
        self.step(3.25)
        self.assertGreater(self.step(3.51).v,0.)

    def test_stop_order_and_terminal_red(self):
        self.drive.event('PERSON_ON','one',2.)
        self.assertFalse(self.drive.event('PERSON_OFF','older',1.9))
        self.assertEqual(self.step(2.1).reason,'PERSON')
        self.drive.event('RED','r',2.2)
        self.assertFalse(self.drive.event('GREEN','g',2.3))
        self.assertEqual(self.step(2.4).reason,'RED')

    def test_checkered_at_next_ordered_line(self):
        self.step()
        self.assertTrue(self.drive.event('CHECKER','checker',1.01))
        for i in range(1,401):self.drive.time_gates((self.drive.path.length*i/400)%self.drive.path.length,1.+i*.1)
        self.assertTrue(self.drive.done)
        self.assertEqual(len(self.drive.timer.laps),1)
        self.assertEqual(self.step(42.).reason,'FINISHED')

    def test_registered_map_without_recon(self):
        r=RaceManager('r')
        self.assertTrue(r.command('r','1','CHECK',{'healthy':True}))
        self.assertFalse(r.command('r','2','RECON',{'guard_ready':True}))
        self.assertFalse(r.command('r','3','MAP_READY',{'map_valid':True}))
        self.assertTrue(r.command('r','4','MAP_READY',dict.fromkeys(('map_valid','path_valid','shared','guard_ready'),True)))
