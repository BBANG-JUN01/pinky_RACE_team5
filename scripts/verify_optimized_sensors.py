import argparse
import importlib.util,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify',root/'scripts/verify_sensor_loop.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from pinky_gp_navigation.raceline import optimize
from pinky_gp_navigation.vehicle_profile import load_profile
p,r=load_profile(root/'src/pinky_gp_bringup/config/racing_sim.json')
grid=m.Occupancy(m.track.WIDTH,m.track.HEIGHT,m.track.RES,m.track.ORIGIN,m.track.occupancy(),r)
q=optimize(m.track.centerline(),grid,p)
original=m.RaceDrive
m.RaceDrive=lambda points,grid,laps:original(q['points'],grid,laps,limits=p.limits,racing_profile=p)
parser=argparse.ArgumentParser()
parser.add_argument('--scenario',choices=['clean','cone','barrier'],default='clean')
parser.add_argument('--seeds',type=int,default=3)
args=parser.parse_args()
if args.seeds<1:parser.error('positive seed count required')
rows=[m.run(i,args.scenario,grid,dense=True) for i in range(args.seeds)]
print(json.dumps(rows,indent=2))

if not all(r['pass'] for r in rows):raise SystemExit(1)
