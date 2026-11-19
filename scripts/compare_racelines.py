"""Three-lap closed-loop A/B scoring with independent world geometry."""
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
for name in ('core','navigation'):
    sys.path.insert(0,str(ROOT/'src'/('pinky_gp_'+name)))
from pinky_gp_navigation import track_fixture as t
from pinky_gp_navigation.scan_race import RaceDrive,Occupancy
from pinky_gp_navigation.vehicle_profile import load_profile
from pinky_gp_navigation.raceline import optimize

p,r=load_profile(ROOT/'src/pinky_gp_bringup/config/racing_sim.json')
grid=Occupancy(t.WIDTH,t.HEIGHT,t.RES,t.ORIGIN,t.occupancy(),r)
opt=optimize(t.centerline(),grid,p)
rows=[]
for label,points in [('reference',t.centerline()),('optimized',opt['points'])]:
    robot=RaceDrive(points,grid,3,limits=p.limits,racing_profile=p)
    x=y=yaw=v=w=0.
    margin=math.inf
    for i in range(2000):
        cmd=robot.step((x,y,yaw),[],(i+1)*.1,v,w)
        if robot.done:break
        v,w=cmd.v,cmd.w
        x+=v*.1*math.cos(yaw+w*.05);y+=v*.1*math.sin(yaw+w*.05);yaw+=w*.1
        margin=min(margin,t.wall_distance(x,y)-r)
        if margin<0:break
    rows.append(dict(path=label,finished=robot.done,laps=robot.timer.laps,min_margin_m=margin))
print(json.dumps({'prediction':opt['optimization'],'closed_loop':rows},indent=2))
assert all(v['finished'] and v['min_margin_m']>0 for v in rows)
assert sum(rows[1]['laps'])<sum(rows[0]['laps'])
