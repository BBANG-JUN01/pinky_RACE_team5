"""Closed-loop differential-drive tracking; no obstacle planner."""
import math
from .path_manager import LoopPath

class PurePursuit:
    def __init__(self, points, lookahead=.25, speed=.15, max_angular=.8, max_error=.35):
        if not all(math.isfinite(v) and v>0 for v in (lookahead,speed,max_angular,max_error)):
            raise ValueError('positive finite configuration required')
        self.path=LoopPath(points)
        self.lookahead,self.speed,self.max_angular,self.max_error=lookahead,speed,max_angular,max_error
        self.segment=None

    def target(self,s):
        s %= self.path.length
        for i,start in reversed(list(enumerate(self.path.starts))):
            if s>=start:
                t=(s-start)/self.path.lengths[i];a=self.path.points[i];b=self.path.points[(i+1)%len(self.path.points)]
                return a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])

    def update(self,x,y,yaw):
        if not all(math.isfinite(v) for v in (x,y,yaw)):raise ValueError('invalid pose')
        p=self.path.project((x,y),self.segment,window=6,max_error=self.max_error)
        self.segment=p['segment'];tx,ty=self.target(p['s']+self.lookahead)
        dx,dy=tx-x,ty-y
        ahead=math.cos(yaw)*dx+math.sin(yaw)*dy
        lateral=-math.sin(yaw)*dx+math.cos(yaw)*dy
        if ahead<=0:raise ValueError('target behind robot; realign while stopped')
        curvature=2*lateral/max(dx*dx+dy*dy,1e-9)
        v=min(self.speed,self.max_angular/max(abs(curvature),1e-9))
        return v,v*curvature,p

class LapProgress:
    """Unwrap progress with physical jump limit and forward checkpoint quarters."""
    def __init__(self,length,max_step):
        if not all(math.isfinite(v) and v>0 for v in (length,max_step)) or max_step>=length/4:
            raise ValueError('invalid progress bounds')
        self.length,self.max_step=length,max_step
        self.last=None;self.total=0.;self.quarters=0
    def update(self,s):
        if not math.isfinite(s) or not 0<=s<self.length:raise ValueError('invalid s')
        if self.last is None:self.last=s;return 0
        delta=(s-self.last+self.length/2)%self.length-self.length/2
        if abs(delta)>self.max_step:raise ValueError('localization jump')
        self.last=s;self.total+=delta
        self.quarters=max(self.quarters,int(max(0.,self.total)/(self.length/4)))
        return self.quarters//4
