"""Guide algorithms: negative paths and a complete synthetic race, no hardware."""
import unittest
import math
import tempfile
from pathlib import Path
from pinky_gp_guard.command_guard import CommandGuard, Velocity
from pinky_gp_guard.robot_health import HealthMonitor
from pinky_gp_recon.wall_follower import wall_command, sector_distance
from pinky_gp_recon.recon_manager import ReconManager
from pinky_gp_recon.map_finalize import manifest
from pinky_gp_navigation.path_manager import LoopPath
from pinky_gp_navigation.grid_manager import GridAligner
from pinky_gp_navigation.nav2_adapter import NavigationSession
from pinky_gp_perception.detector import normalize
from pinky_gp_perception.range_association import associate
from pinky_gp_perception.grid_reader import select_target
from pinky_gp_perception.signal_reader import StartLights
from pinky_gp_race.race_manager import RaceManager
from pinky_gp_race.progress_manager import ProgressManager, ranking
from pinky_gp_race.penalty_manager import PenaltyManager
from pinky_gp_behavior.behavior_manager import OvertakeManager
from pinky_gp_behavior.speed_policy import speed_limit
from pinky_gp_core.policy import RacePolicy, StopReasons
from pinky_gp_display.display_manager import frame, format_time
from pinky_gp_dashboard.operator_server import OperatorCommand

class GuideTests(unittest.TestCase):
    def test_guard_default_disabled(self):
        self.assertEqual(CommandGuard().evaluate(Velocity('nav',.1,0.,1.),1.,'RACING')[:2],(0.,0.))
    def test_guard_rejects_wrong_owner_and_future(self):
        g=CommandGuard()
        for c in [Velocity('recon',.1,0.,1.),Velocity('nav',.1,0.,2.),Velocity('nav',math.nan,0.,1.)]:
            self.assertEqual(g.evaluate(c,1.,'RACING',enabled=True)[:2],(0.,0.))
    def test_guard_curvature_and_stop(self):
        g=CommandGuard();c=Velocity('nav',.3,.2,1.)
        v,w,_=g.evaluate(c,1.,'RACING',enabled=True)
        self.assertAlmostEqual(w/v,.2/.3)
        self.assertEqual(g.evaluate(c,1.,'RACING',stops=['PERSON'],enabled=True)[:2],(0.,0.))
    def test_health_missing_stale_and_reverse_clock(self):
        h=HealthMonitor({'scan':.3});self.assertEqual(h.faults(0.),['scan'])
        h.touch('scan',1.);self.assertEqual(h.faults(1.1),[])
        self.assertEqual(h.faults(2.),['scan']);self.assertEqual(h.faults(.5),['scan'])
    def test_wall_invalid_and_front_blocked(self):
        self.assertIsNone(sector_distance([math.inf,math.nan],.1,10.))
        self.assertEqual(wall_command(.1,.3)[:2],(0.,0.))
        self.assertGreater(wall_command(1.,.5)[1],0.)
    def test_recon_requires_departure_and_distance(self):
        r=ReconManager();r.start(0.)
        self.assertEqual(r.update(1.,4.,True,True,True,True),'RECON')
        r.update(2.,1.,False,False,True,True)
        self.assertEqual(r.update(3.,4.,True,True,True,True),'RETURNED')
    def test_recon_timeout(self):
        r=ReconManager();r.start(0.)
        self.assertEqual(r.update(121.,4.,True,True,True,True),'FAILED')
    def test_manifest_requires_verification_and_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=[Path(tmp)/name for name in ('map.yaml','map.pgm','path.json')]
            for p in paths:p.write_text('data')
            with self.assertRaises(ValueError):manifest(*paths)
            self.assertEqual(len(manifest(*paths,geometry_checked=True)['files']),3)
    def test_path_projects_to_segment_not_waypoint(self):
        p=LoopPath([(0,0),(2,0),(2,1),(0,1)])
        self.assertEqual(p.length,6.)
        self.assertAlmostEqual(p.project((.7,.1),0,0)['s'],.7)
        with self.assertRaises(ValueError):p.project((10.,10.))
    def test_path_degenerate(self):
        with self.assertRaises(ValueError):LoopPath([(0,0),(0,0),(1,1)])
    def test_grid_requires_stable_stop_and_clears_on_loss(self):
        g=GridAligner()
        for _ in range(4):self.assertEqual(g.update(0,0,0,True,True,False)[2],'SETTLING')
        for _ in range(3):last=g.update(0,0,0,True,True,True)
        self.assertEqual(last[2],'READY')
        self.assertEqual(g.update(0,0,0,False,True,True)[2],'WAIT_VALID_TARGET')
    def test_nav_cancel_ack_blocks_replacement(self):
        n=NavigationSession();self.assertTrue(n.request('a',True,True));n.accepted('a',True);n.cancel()
        self.assertFalse(n.request('b',True,True));self.assertFalse(n.result('wrong',success=True))
        n.result('a',canceled=True);self.assertTrue(n.request('b',True,True))
    def test_detector_filters_invalid_boxes(self):
        rows=[{'label':'person','confidence':.9,'xyxy':[-1,0,10,10]}]
        self.assertEqual(normalize(rows,640,480,1.),[])
    def test_range_requires_calibration_and_sync(self):
        self.assertFalse(associate([1.,1.,1.],1.,1.)['valid'])
        self.assertFalse(associate([1.,1.,1.],1.,2.,True)['valid'])
        self.assertFalse(associate([.5,1.,2.],1.,1.,True)['valid'])
    def test_grid_duplicate_marker_invalid(self):
        m={'id':1,'captured_at':1.,'pose':[0,0,0]}
        self.assertIsNone(select_target([m,m],1,1.))
        self.assertIsNone(select_target([m],1,2.))
    def test_lights_require_sequence_and_fresh_roi(self):
        s=StartLights(2,1)
        self.assertFalse(s.observe(2,1.));self.assertFalse(s.observe(0,2.))
        s.observe(1,3.);s.observe(2,4.)
        self.assertFalse(s.observe(0,5.,roi_visible=False))
        self.assertFalse(s.observe(0,6.))
        s.observe(1,7.);s.observe(2,8.);self.assertTrue(s.observe(0,9.))
        self.assertFalse(s.observe(0,10.))
    def test_race_rejects_invalid_transitions_and_deduplicates(self):
        r=RaceManager('r')
        self.assertFalse(r.command('wrong','1','RED'))
        self.assertFalse(r.command('r','2','START',{'lights_valid':True}))
        self.assertTrue(r.command('r','3','CHECK',{'healthy':True}))
        self.assertTrue(r.command('r','3','CHECK',{'healthy':True}))
        self.assertEqual(r.phase,'CHECKING')
    def test_red_is_terminal(self):
        r=RaceManager('r');r.command('r','red','RED')
        r.signals([('r','green','GREEN',2.)]);self.assertEqual(r.phase,'ABORTED')
        self.assertFalse(r.command('r','4','CHECK',{'healthy':True}))
    def test_full_race_and_individual_finish(self):
        r=RaceManager('r')
        evidence=dict.fromkeys(['healthy','guard_ready','map_valid','path_valid','shared','localized','both_ready','lights_valid'],True)
        for i,cmd in enumerate(['CHECK','MAP_READY','GRID','ARM_START','START']):
            self.assertTrue(r.command('r',str(i),cmd,evidence))
        p=ProgressManager();p.start(0.)
        self.assertFalse(p.gate('A','FINISH',.1))
        p.checker=True;r.command('r','checker','CHECKER')
        for robot,end in [('A',3.),('B',4.)]:
            p.gate(robot,'CP1',1.);p.gate(robot,'CP2',2.);p.gate(robot,'FINISH',end)
        self.assertEqual(p.snapshot('A',10.)['last'],3.)
        self.assertEqual(p.snapshot('B',10.)['last'],4.)
        self.assertTrue(r.command('r','finish','FINISH',{'all_finished':True,'all_stopped':True}))
    def test_rank_ties(self):
        self.assertEqual(ranking({'A':(1,.5),'B':(1,.5)},4.),{'A':1,'B':1})
    def test_penalty_stale_odom_resets_continuous_timer(self):
        p=PenaltyManager();p.issue('1','A',2.)
        p.update('A',0.,True,True);p.update('A',1.,True,False)
        self.assertEqual(p.update('A',2.,True,True)['remaining'],2.)
        self.assertFalse(p.update('A',4.,True,True)['stop'])
        self.assertFalse(p.issue('1','A',2.))
    def test_overtake_aborts_under_sc(self):
        o=OvertakeManager();o.update(True,True);o.update(zone=True,candidate_clear=True,merge_clear=True)
        self.assertEqual(o.update(restriction='SC'),'ABORT')
    def test_speed_drs_disabled_for_sc_and_person(self):
        r=RacePolicy('r');stops=StopReasons()
        self.assertTrue(speed_limit(r,stops,0.,2.,True,True,True)[1])
        r.signals([('r','1','SC_ON',1.)])
        self.assertEqual(speed_limit(r,stops,0.,2.,True,True,True),(.06,False))
        stops.set('PERSON',True)
        self.assertEqual(speed_limit(r,stops,0.,2.,True,True,True),(0.,False))
    def test_display_priorities_and_timing(self):
        self.assertEqual(format_time(12.34),'00:12.34')
        self.assertEqual(format_time(None),'--:--.--')
        self.assertEqual(frame('A',1,1,1.,fresh=True,drs_active=True,stops=['PERSON'])['led'],'RED')
        stale=frame('A',1,1,1.,fresh=False,drs_active=True)
        self.assertEqual(stale['led'],'RED')
        self.assertEqual(stale['lines'][1],'CURRENT --:--.--')
        self.assertEqual(frame('A',1,1,0.,fresh=True,finished=True,stops=['FINISHED'])['primary'],'FINISHED')
    def test_operator_rejects_direct_start(self):
        with self.assertRaises(ValueError):OperatorCommand.build('r','START',1.)
        with self.assertRaises(ValueError):OperatorCommand.build('r','PENALTY',1.,'A',-1.)

if __name__=='__main__':unittest.main()

