from pathlib import Path
import sys, unittest
root=Path(__file__).resolve().parents[1]
for package in (root/'src').glob('pinky_gp_*'):
    sys.path.insert(0,str(package))
suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
