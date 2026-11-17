"""Synthetic policy example only: no perception, ROS, or movement."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/pinky_gp_core'))
from pinky_gp_core.policy import RacePolicy, StopReasons, effective_speed
from pinky_gp_core.display import display_state
p=RacePolicy('demo');s=StopReasons()
for at,kind in [(1,'YELLOW'),(2,'GREEN'),(3,'SC_ON'),(4,'GREEN'),(5,'RED'),(6,'GREEN')]:
    p.signals([('demo',str(at),kind,at)])
    s.set('RED',p.aborted)
    cap,on=effective_speed(.1,.3,.3,p,s,True,.2,True,True,True)
    print(kind,'restriction=',p.restriction.value,'aborted=',p.aborted,'cap=',cap,
          'display=',display_state(s.reasons,p.restriction.value,on,fresh=True))
