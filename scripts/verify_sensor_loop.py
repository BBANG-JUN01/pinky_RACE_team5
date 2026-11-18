"""Independent ray-cast and unicycle fixture for the same controller used by ROS."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1]
for name in ('core','navigation','guard'):
    sys.path.insert(0,str(ROOT/'src'/('pinky_gp_'+name)))
from pinky_gp_navigation import track_fixture as track
from pinky_gp_navigation.scan_race import Occupancy, RaceDrive, RADIUS, scan_points


def run(seed,scenario,grid,dense=False):
    rng=random.Random(seed)
    drive=RaceDrive(track.centerline(),grid,3 if scenario=='clean' else 1)
    x,y,theta=0.,rng.uniform(-.016,.016),rng.uniform(-.035,.035)
    v=w=0.
    gap=float('inf')
    bypass=blocked=0
    removed=False
    truth_gates=0
    last_x=x
    for tick in range(2200):
        now=(tick+1)*.1
        boxes=track.WALLS
        if scenario in ('cone','barrier') and tick>=2 and not removed:
            boxes+= (track.EVENT_BOXES[scenario],)
        if scenario=='barrier' and blocked>=15:
            removed=True
        clearance=track.wall_distance(x,y,boxes)-RADIUS
        gap=min(gap,clearance)
        if gap<0: break
        lx,ly=x-.017*math.cos(theta),y-.017*math.sin(theta)
        heading=theta+math.pi
        beams=640 if dense else 96
        step=2*math.pi/(beams-1)
        ranges=[track.ray(lx,ly,heading-math.pi+i*step,boxes)+rng.gauss(0,.02 if dense else .003) for i in range(beams)]
        hits=scan_points(ranges,-math.pi,step,.05,12.,(lx,ly,heading))
        cmd=drive.step((x+rng.uniform(-.001,.001),y+rng.uniform(-.001,.001),theta),hits,now,v,w)
        bypass+=cmd.reason=='BYPASS'
        blocked+=cmd.reason in ('NO_CLEAR_LANE','BRAKING_ARC_BLOCKED','FOOTPRINT_BLOCKED')
        if {'right':x>1.,'top':y>1.2 and abs(x)<.4,'left':x<-1.,
            'line':y<.25 and last_x<-.04<=x}[('right','top','left','line')[truth_gates%4]]:
            truth_gates+=1
        if drive.done: break
        last_x=x
        v=cmd.v*rng.uniform(.985,1.015)
        w=cmd.w*rng.uniform(.985,1.015)
        mid=theta+w*.05
        x+=.1*v*math.cos(mid); y+=.1*v*math.sin(mid); theta+=w*.1
    ok=(drive.done and truth_gates//4==drive.goal and gap>=0 and
        (scenario!='cone' or bypass>0) and (scenario!='barrier' or removed and blocked>=15))
    return {'scenario':scenario,'rays':beams,'noise_sd_m':.02 if dense else .003,'seed':seed,'pass':ok,'laps':len(drive.timer.laps),
            'truth_laps':truth_gates//4,'laps_s':[round(t,3) for t in drive.timer.laps],
            'min_margin_m':round(gap,4),'bypass_frames':bypass,'blocked_frames':blocked,
            'last_state':cmd.reason,'elapsed_s':round(now,2)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,default=5)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.seeds<1: p.error('positive seed count required')
    grid=Occupancy(track.WIDTH,track.HEIGHT,track.RES,track.ORIGIN,track.occupancy())
    rows=[]
    for i in range(a.seeds):
        for scenario in ('clean','cone','barrier'):
            row=run(i,scenario,grid);rows.append(row)
            print(json.dumps(row),flush=True)
    for i in range(min(3,a.seeds)):
        row=run(i,'cone',grid,dense=True);rows.append(row);print(json.dumps(row),flush=True)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps({'environment':'raycast_kinematic','results':rows},indent=2)+'\n')
    return int(not all(r['pass'] for r in rows))


if __name__=='__main__': sys.exit(main())
