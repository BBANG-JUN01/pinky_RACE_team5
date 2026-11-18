"""Advance only after successful gates and preserve every measurement and failure."""
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
    p.add_argument('--bag',action='store_true',help='record all ROS trials')
    p.add_argument('--reuse-slam-map',action='store_true',help='rebuild a map from the final bag and race on it')
    a=p.parse_args()
    if a.through=='software' and a.reuse_slam_map: p.error('map replay requires ROS')
    out=(a.output/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    out.mkdir(parents=True);print('Results:',out,flush=True)
    index={'requested':a.through,'passed':False,'stages':[]}
    def save():
        (out/'summary.json').write_text(json.dumps(index,indent=2)+'\n')
    def stage(name,cmd):
        print('Running',name,flush=True)
        logfile=out/(name+'.log')
        with logfile.open('w') as log:
            result=subprocess.run([sys.executable,str(ROOT/'scripts'/cmd[0]),*cmd[1:]],
                                   cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        index['stages'].append({'stage':name,'exit_code':result.returncode});save()
        if result.returncode:
            print('FAILED',name,'see',logfile,flush=True)
            print('\n'.join(logfile.read_text(errors='replace').splitlines()[-10:]),flush=True)
            return False
        return True
    if not stage('regression',['validate_weekday.py']): return 1
    if not stage('sensor_sweep',['verify_sensor_loop.py','--seeds','8','--output',str(out/'raycast.json')]): return 1
    backends=['ros_fixture','gazebo'][:{'software':0,'ros':1,'gazebo':2}[a.through]]
    for backend in backends:
        base=['run_single_trial.py','--backend',backend,'--domain',str(a.domain)]
        for i,case in enumerate(['clean','cone','barrier','rules','watchdog','clean']):
            name=f'{backend}_{i}_{case}'
            trial=out/name
            cmd=base+['--case',case,'--seed',str(i),'--output',str(trial)]
            last=backend==backends[-1] and i==5
            if a.bag or (last and a.reuse_slam_map): cmd.append('--bag')
            if not stage(name,cmd): return 1
    if a.reuse_slam_map:
        bags=list(trial.glob('*/bag/metadata.yaml'))
        if len(bags)!=1:
            index['failure']='missing completed final clean bag';save();print(index['failure']);return 1
        registered=out/'registered'
        if not stage('slam_registration',['register_from_bag.py',str(bags[0].parent),str(registered),
                                          '--domain',str(a.domain),'--rate','1.5']): return 1
        if not stage('registered_map_race',base+['--case','clean','--seed','19','--map-file',
                           str(registered/'map.yaml'),'--output',str(out/'registered_map_race')]): return 1
    index['passed']=True;save()
    print('PASS through',a.through,flush=True)
    return 0


if __name__=='__main__': sys.exit(main())
