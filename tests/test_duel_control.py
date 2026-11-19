import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('duel',Path(__file__).parents[1]/'scripts/duel_control.py')
duel=importlib.util.module_from_spec(spec);spec.loader.exec_module(duel)
class DuelTests(unittest.TestCase):
    def test_partial_start_stops_both(self):
        calls=[]
        def fake(d,a):
            calls.append((d,a));return d,not(d==42 and a=='start'),'test'
        result=duel.operate([41,42],'start',fake)
        self.assertEqual(len(result),4)
        self.assertIn((41,'stop'),calls);self.assertIn((42,'stop'),calls)
    def test_success_does_not_stop(self):
        calls=[]
        def fake(d,a):calls.append((d,a));return d,True,''
        self.assertEqual(len(duel.operate([41,42],'start',fake)),2)
        self.assertEqual(set(calls),{(41,'start'),(42,'start')})
