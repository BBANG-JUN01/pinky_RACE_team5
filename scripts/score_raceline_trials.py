"""Compare independent Gazebo runs; missing evidence never counts as success."""
import argparse
import json
from pathlib import Path
from statistics import mean
p=argparse.ArgumentParser()
p.add_argument('baseline',type=Path)
p.add_argument('optimized',type=Path)
a=p.parse_args()
def read(folder):
    reports=[json.loads(f.read_text()) for f in folder.rglob('result.json')]
    if len(reports)!=1:raise ValueError('exactly one run required per comparison folder')
    r=reports[0]
    if not r['passed'] or r['truth_laps']!=3 or r['min_margin_m']<=0 or len(r['lap_times_s'])!=3:
        raise ValueError('three collision-free independently judged laps required')
    return r
b,o=read(a.baseline),read(a.optimized)
bt,ot=mean(b['lap_times_s'][1:]),mean(o['lap_times_s'][1:])
print(json.dumps(dict(baseline_s=bt,optimized_s=ot,improvement_percent=100*(bt-ot)/bt,
                     optimized_min_margin_m=o['min_margin_m']),indent=2))
if ot>=bt:raise SystemExit('candidate rejected: measured improvement required')
