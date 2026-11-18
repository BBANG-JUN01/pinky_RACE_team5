"""Run software checks; does not imply ROS/Gazebo or physical validation."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
commands=[['scripts/check_core.py'],['scripts/check_guard.py'],['scripts/guide_smoke.py'],['scripts/simulate_laps.py','--seeds','10']]
for args in commands:
    print('RUN',*args,flush=True)
    result=subprocess.run([sys.executable,*args],cwd=root)
    if result.returncode:raise SystemExit(result.returncode)
print('PASS: software and kinematic checks only; Gazebo/ROS integration remains unverified')
