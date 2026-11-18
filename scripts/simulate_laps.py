"""Deterministic kinematic integration test, NOT Gazebo/SLAM validation."""
import argparse,json,math,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src/pinky_gp_navigation'))
from pinky_gp_navigation.pure_pursuit import PurePursuit,LapProgress

def simulate(seed=0,laps=3):
    import random
    rng=random.Random(seed)
    points=[(1.5*math.cos(i*2*math.pi/160),math.sin(i*2*math.pi/160)) for i in range(160)]
    c=PurePursuit(points);tracker=LapProgress(c.path.length,.1)
    x,y,yaw=1.5+rng.uniform(-.03,.03),0.,math.pi/2+rng.uniform(-.03,.03)
    dt=.05;worst=0.;completed=0
    for step in range(15000):
        v,w,p=c.update(x,y,yaw);completed=tracker.update(p['s']);worst=max(worst,p['error'])
        if completed>=laps:break
        # Exact unicycle integration, bounded actuator perturbation.
        v*=rng.uniform(.99,1.01);w*=rng.uniform(.99,1.01)
        if abs(w)>1e-9:
            x+=v/w*(math.sin(yaw+w*dt)-math.sin(yaw));y-=v/w*(math.cos(yaw+w*dt)-math.cos(yaw))
        else:x+=v*math.cos(yaw)*dt;y+=v*math.sin(yaw)*dt
        yaw+=w*dt
    return {'environment':'synthetic_kinematic','seed':seed,'laps':completed,'seconds':step*dt,'max_tracking_error_m':worst,'passed':completed>=laps and worst<.15}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=10);a=p.parse_args()
    if a.seeds<1:p.error('seeds must be positive')
    results=[simulate(i) for i in range(a.seeds)];print(json.dumps(results,indent=2));raise SystemExit(not all(r['passed'] for r in results))
