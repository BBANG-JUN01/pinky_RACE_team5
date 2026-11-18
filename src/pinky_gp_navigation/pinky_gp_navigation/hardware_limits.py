"""Measured limits, not manufacturer maximums. SI units."""
import math
from dataclasses import dataclass
@dataclass(frozen=True)
class Limits:
    speed:float
    braking:float
    latency:float
    margin:float
    lateral_accel:float
    angular:float
    def __post_init__(self):
        if not all(math.isfinite(v) and v>0 for v in vars(self).values()):raise ValueError('positive measured limits required')
    def clearance_cap(self,distance):
        if not math.isfinite(distance):return 0.
        d=max(0.,distance-self.margin);a=self.braking;t=self.latency
        return min(self.speed,max(0.,math.sqrt((a*t)**2+2*a*d)-a*t))
    def corner_cap(self,curvature):
        if not math.isfinite(curvature):return 0.
        k=abs(curvature)
        return min(self.speed,math.sqrt(self.lateral_accel/max(k,1e-9)),self.angular/max(k,1e-9))
def speed_profile(points,limits):
    n=len(points)
    if n<3 or any(not all(math.isfinite(v) for v in p) for p in points):raise ValueError('invalid points')
    distances=[math.dist(points[i],points[(i+1)%n]) for i in range(n)]
    if min(distances)<=1e-6:raise ValueError('duplicate points')
    caps=[]
    for i in range(n):
        a,b,c=points[i-1],points[i],points[(i+1)%n]
        cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        denom=math.dist(a,b)*math.dist(b,c)*math.dist(a,c)
        if denom<=1e-9:raise ValueError('degenerate turn')
        caps.append(limits.corner_cap(2*cross/denom))
    # Bellman relaxations propagate braking limits backwards around the loop.
    for _ in range(n):
        changed=False
        for i in reversed(range(n)):
            cap=min(caps[i],math.sqrt(caps[(i+1)%n]**2+2*limits.braking*distances[i]))
            changed|=cap<caps[i]-1e-12;caps[i]=cap
        if not changed:break
    return caps
