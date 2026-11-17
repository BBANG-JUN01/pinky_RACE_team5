import unittest
from pinky_gp_core.policy import RacePolicy, Restriction, StopReasons, Penalty, effective_speed, drs_gap
from pinky_gp_core.timing import LapTimer
from pinky_gp_core.display import display_state

class CoreTests(unittest.TestCase):
    def test_red_is_terminal(self):
        p=RacePolicy('r');p.signals([('r','1','RED',1)]);p.signals([('r','2','GREEN',2)])
        self.assertTrue(p.aborted)
    def test_batch_red_wins(self):
        p=RacePolicy('r');p.signals([('r','1','RED',1),('r','2','GREEN',2)])
        self.assertTrue(p.aborted)
    def test_wrong_race(self):
        p=RacePolicy('r');p.signals([('old','1','RED',1)]);self.assertFalse(p.aborted)
    def test_duplicate(self):
        p=RacePolicy('r');p.signals([('r','1','YELLOW',1),('r','1','GREEN',2)])
        self.assertEqual(p.restriction,Restriction.YELLOW)
    def test_stale_green(self):
        p=RacePolicy('r');p.signals([('r','1','YELLOW',10),('r','2','GREEN',9)])
        self.assertEqual(p.restriction,Restriction.YELLOW)
    def test_equal_green_does_not_unlock(self):
        p=RacePolicy('r');p.signals([('r','1','GREEN',1),('r','2','YELLOW',1)])
        self.assertEqual(p.restriction,Restriction.YELLOW)
    def test_sc_survives_yellow(self):
        p=RacePolicy('r');p.signals([('r','1','SC_ON',1),('r','2','YELLOW',2)])
        self.assertEqual(p.restriction,Restriction.SC)
        p.signals([('r','3','GREEN',3)]);self.assertEqual(p.restriction,Restriction.NORMAL)
    def test_independent_stop_reasons(self):
        s=StopReasons();s.set('PERSON',True);s.set('PENALTY',True);s.set('PENALTY',False)
        self.assertTrue(s.stopped)
    def test_penalty_waits_for_actual_stop(self):
        p=Penalty(3);self.assertEqual(p.update(10,False),3)
        self.assertEqual(p.update(20,True),3);self.assertEqual(p.update(22,True),1)
        self.assertEqual(p.update(23,True),0)
    def test_penalty_motion_resets_timer(self):
        p=Penalty(3);p.update(1,True);p.update(2,True);self.assertEqual(p.update(3,False),3)
    def test_invalid_penalty(self):
        with self.assertRaises(ValueError):Penalty(float('nan'))
    def test_drs_cannot_override_stop(self):
        v,on=effective_speed(.1,.3,.3,RacePolicy('r'),StopReasons({'PERSON'}),True,.2,True,True,True)
        self.assertEqual((v,on),(0.,False))
    def test_yellow_blocks_drs(self):
        p=RacePolicy('r',restriction=Restriction.YELLOW)
        self.assertEqual(effective_speed(.1,.3,.08,p,StopReasons(),True,.2,True,True,True),(.08,False))
    def test_drs_is_effective_not_only_requested(self):
        p=RacePolicy('r');s=StopReasons()
        self.assertEqual(effective_speed(.1,.3,.08,p,s,True,.2,True,True,True),(.08,False))
        self.assertEqual(effective_speed(.1,.3,.3,p,s,True,.2,True,True,True),(.2,True))
    def test_stale_data_stops(self):
        self.assertEqual(effective_speed(.1,.3,.3,RacePolicy('r'),StopReasons()),(0.,False))
    def test_gap_direction_and_lap(self):
        self.assertTrue(drs_gap(1,1.5,10,True,True,True,1))
        self.assertFalse(drs_gap(9,.2,10,True,True,True,1))
        self.assertFalse(drs_gap(1,1.5,10,False,True,True,1))
    def test_ordered_lap(self):
        t=LapTimer(('c1','c2','finish'));t.start(0)
        self.assertFalse(t.gate('finish',1));t.gate('c1',2);t.gate('c2',3);t.gate('finish',4)
        self.assertEqual((t.last,t.best),(4,4))
    def test_reverse_gate_rejected(self):
        t=LapTimer(('c1','finish'));t.start(0);self.assertFalse(t.gate('c1',1,False))
    def test_timer_freezes(self):
        t=LapTimer(('c1','finish'));t.start(0);t.freeze(5);self.assertEqual(t.current(100),5)
        self.assertIsNone(t.best)
    def test_display_priorities(self):
        self.assertEqual(display_state({'PERSON'},drs_active=True,fresh=True)[0],'RED')
        self.assertEqual(display_state(set(),drs_active=True,fresh=True)[0],'GREEN')
        self.assertEqual(display_state(set(),drs_active=True,fresh=False)[0],'RED')

if __name__=='__main__':unittest.main()
