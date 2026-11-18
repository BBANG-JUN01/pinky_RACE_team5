"""Read-only ROS inventory; run once per robot after sourcing its ROS setup."""
import argparse, json, os, platform, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--robot',required=True,choices=['robot_a','robot_b']);p.add_argument('--output',required=True);a=p.parse_args()
commands=[['ros2','topic','list','-t'],['ros2','node','list'],['ros2','service','list','-t']]
result={'robot':a.robot,'host':platform.node(),'ros_distro':os.getenv('ROS_DISTRO'),'verified':False,'checks':[]}
for cmd in commands:
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
        result['checks'].append({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    except (OSError,subprocess.TimeoutExpired) as e:
        result['checks'].append({'command':cmd,'error':str(e)})
with Path(a.output).open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(a.output)
raise SystemExit(0 if all(c.get('returncode')==0 for c in result['checks']) else 1)
