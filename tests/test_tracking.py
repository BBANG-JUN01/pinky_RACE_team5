import math,unittest
from pinky_gp_navigation.pure_pursuit import PurePursuit,LapProgress
class TrackingTests(unittest.TestCase):
    def controller(self):return PurePursuit([(0,0),(2,0),(2,1),(0,1)])
    def test_straight(self):
        v,w,_=self.controller().update(.1,0,0);self.assertGreater(v,0);self.assertAlmostEqual(w,0)
    def test_outside(self):
        with self.assertRaises(ValueError):self.controller().update(10,10,0)
    def test_nan(self):
        with self.assertRaises(ValueError):self.controller().update(0,0,float('nan'))
    def test_wrong_heading(self):
        with self.assertRaises(ValueError):self.controller().update(.1,0,math.pi)
    def test_limits(self):
        v,w,_=self.controller().update(.1,.1,0);self.assertLessEqual(v,.15);self.assertLessEqual(abs(w),.8)
    def test_progress_jump(self):
        p=LapProgress(10,.2);p.update(0)
        with self.assertRaises(ValueError):p.update(2)
    def test_finish_jitter(self):
        p=LapProgress(10,.2)
        for s in [9.99,.01,9.99,.01]*20:self.assertEqual(p.update(s),0)
    def test_reverse(self):
        p=LapProgress(10,.2)
        for i in range(301):self.assertEqual(p.update((-i*.05)%10),0)
    def test_three_laps(self):
        p=LapProgress(10,.2)
        for i in range(602):lap=p.update((i*.05)%10)
        self.assertEqual(lap,3)
