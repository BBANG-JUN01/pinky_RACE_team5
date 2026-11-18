from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pinky_gp_guard'))
from pinky_gp_guard.guard_core import CommandGuard
class Tests(unittest.TestCase):
    def ready(self):
        g=CommandGuard(.2,1.,.5);g.select('race')
        for n in g.required:g.observe(n,1.)
        g.receive('race',.1,.2,1.);return g
    def test_normal(self):self.assertEqual(self.ready().tick(1.1),(.1,.2,()))
    def test_timeout(self):self.assertEqual(self.ready().tick(2.)[:2],(0.,0.))
    def test_wrong_source(self):
        g=self.ready();self.assertFalse(g.receive('recon',1.,1.,1.));self.assertEqual(g.tick(1.)[0],.1)
    def test_switch(self):
        g=self.ready();g.select('grid');self.assertEqual(g.tick(1.)[0],0.)
    def test_overlap(self):
        g=self.ready();g.stop('PERSON');g.stop('PENALTY');g.stop('PENALTY',False);self.assertIn('PERSON',g.tick(1.)[2])
    def test_no_replay(self):
        g=self.ready();g.stop('PERSON');g.stop('PERSON',False);self.assertEqual(g.tick(1.)[0],0.)
    def test_nan(self):
        g=self.ready();self.assertFalse(g.receive('race',float('nan'),0.,1.));self.assertEqual(g.tick(1.)[0],0.)
    def test_scaling(self):
        g=self.ready();g.receive('race',.4,1.,1.);self.assertEqual(g.tick(1.)[:2],(.2,.5))
    def test_clock_rollback(self):
        g=self.ready();g.tick(1.);self.assertEqual(g.tick(.9)[0],0.)
    def test_future_sensor(self):
        g=self.ready();g.observe('scan',2.);self.assertEqual(g.tick(1.)[0],0.)
    def test_reverse(self):
        g=self.ready();g.receive('race',-.1,0.,1.);self.assertEqual(g.tick(1.)[0],0.)
    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):CommandGuard(0.,1.,.5)
unittest.main()
