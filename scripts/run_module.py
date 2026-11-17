"""소스 checkout에서 colcon 없이 모듈 예제 실행."""
from pathlib import Path
import importlib,sys
root=Path(__file__).resolve().parents[1]
for package in (root/'src').glob('pinky_gp_*'): sys.path.insert(0,str(package))
if len(sys.argv)<2: raise SystemExit('usage: python3 scripts/run_module.py race.race_manager --demo')
package,module=sys.argv[1].split('.',1)
importlib.import_module(f'pinky_gp_{package}.{module}').main(sys.argv[2:])
