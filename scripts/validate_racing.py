"""Run testing gates in order. Stop at the first failure and retain its artifacts."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--through',choices=['software','ros','gazebo'],default='gazebo')
    p.add_argument('--output',type=Path,default=ROOT/'log/gp_validation')
    p.add_argument('--domain',type=int,default=82)
    p.add_argument('--bag',action='store_true')
    a=p.parse_args()
    out=(a.output/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    out.mkdir(parents=True);print('Results:',out,flush=True)
    jobs=[('regression',['validate_weekday.py']),('sensor_sweep',['verify_sensor_loop.py','--seeds','8',
                                                               '--output',str(out/'raycast.json')])]
    for backend in ['ros_fixture','gazebo'][:{'software':0,'ros':1,'gazebo':2}[a.through]]:
        for index,case in enumerate(['clean','cone','barrier','rules','watchdog','clean']):
            cmd=['run_single_trial.py','--backend',backend,'--case',case,'--seed',str(index),
                 '--domain',str(a.domain),'--output',str(out)]
            if a.bag: cmd.append('--bag')
            jobs.append((f'{backend}_{index}_{case}',cmd))
    index={'requested':a.through,'passed':False,'stages':[]}
    for name,cmd in jobs:
        print('Running',name,flush=True)
        with (out/(name+'.log')).open('w') as log:
            result=subprocess.run([sys.executable,str(ROOT/'scripts'/cmd[0]),*cmd[1:]],
                                   cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        index['stages'].append({'stage':name,'exit_code':result.returncode})
        index['passed']=(result.returncode==0 and name==jobs[-1][0])
        (out/'summary.json').write_text(json.dumps(index,indent=2)+'\n')
        if result.returncode:
            print('FAILED',name,'see',out/(name+'.log'),flush=True)
            return 1
    print('PASS through',a.through,flush=True)
    return 0


if __name__=='__main__': sys.exit(main())
