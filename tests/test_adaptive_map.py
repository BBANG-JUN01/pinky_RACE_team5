import unittest
from pinky_gp_navigation.adaptive_map import AdaptiveMap
from pinky_gp_navigation.hardware_limits import Limits,speed_profile
class AdaptiveTests(unittest.TestCase):
    def grid(self):return AdaptiveMap(30,20,.1,[0]*600,.11)
    def test_detour(self):
        g=self.grid();g.observe([(1.5,1.)],1.,2.)
        path=g.plan((.5,1.),(2.5,1.),1.1)
        self.assertTrue(any(abs(y-1.)>.149 for x,y in path))
        self.assertTrue(all(g.cell(p) not in g.blocked(1.1) for p in path))
    def test_expiration(self):
        g=self.grid();g.observe([(1.5,1.)],1.,2.);self.assertIn((15,10),g.blocked(2.));self.assertNotIn((15,10),g.blocked(4.))
    def test_no_route(self):
        g=self.grid();g.observe([(1.5,i*.1) for i in range(20)],1.,2.)
        with self.assertRaises(ValueError):g.plan((.5,1.),(2.5,1.),2.)
    def test_static_preserved(self):
        g=AdaptiveMap(10,10,.1,[-1]*100,.1)
        with self.assertRaises(ValueError):g.plan((.3,.3),(.6,.6),1.)
    def test_limits(self):
        l=Limits(.3,.4,.2,.1,.2,.8)
        self.assertEqual(l.clearance_cap(.1),0)
        v=l.clearance_cap(.2);self.assertLessEqual(v*.2+v*v/.8+.1,.2000001)
        self.assertLessEqual(l.corner_cap(4),.2)
    def test_braking(self):
        l=Limits(.8,.2,.1,.1,.1,1.)
        p=[(0,0),(1,0),(2,0),(2,1),(1,1),(0,1)];v=speed_profile(p,l)
        import math
        for i in range(len(p)):self.assertLessEqual(v[i]**2,v[(i+1)%len(p)]**2+2*l.braking*math.dist(p[i],p[(i+1)%len(p)])+1e-9)
