"""Bounded minimum-time search on a registered track. SI units, no global optimum claim."""
import math
from dataclasses import dataclass
from .hardware_limits import speed_profile
from .path_manager import LoopPath


@dataclass(frozen=True)
class RacingProfile:
    limits: object
    acceleration: float = .35
    wheel_speed: float = .28
    wheel_separation: float = .0961

    def __post_init__(self):
        if any(not math.isfinite(v) or v<=0 for v in
               (self.acceleration,self.wheel_speed,self.wheel_separation)):
            raise ValueError('positive racing limits required')


def curvature(points):
    out=[]
    for i,b in enumerate(points):
        a,c=points[i-1],points[(i+1)%len(points)]
        area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        denom=math.dist(a,b)*math.dist(b,c)*math.dist(a,c)
        if denom<1e-9: raise ValueError('degenerate racing path')
        out.append(2*area/denom)
    return out


def trajectory(points,profile):
    """Periodic acceleration/braking envelope with per-wheel and corner constraints."""
    LoopPath(points)
    ds=[math.dist(p,points[(i+1)%len(points)]) for i,p in enumerate(points)]
    ks=curvature(points)
    speeds=speed_profile(points,profile.limits)
    speeds=[min(v,profile.wheel_speed/(1+abs(k)*profile.wheel_separation/2))
            for v,k in zip(speeds,ks)]
    n=len(points)
    for _ in range(n):
        changed=False
        for i in range(n):
            j=(i+1)%n
            v=min(speeds[j],math.sqrt(speeds[i]**2+2*profile.acceleration*ds[i]))
            changed|=v<speeds[j]-1e-10
            speeds[j]=v
        for i in reversed(range(n)):
            v=min(speeds[i],math.sqrt(speeds[(i+1)%n]**2+2*profile.limits.braking*ds[i]))
            changed|=v<speeds[i]-1e-10
            speeds[i]=v
        if not changed: break
    seconds=sum(2*d/(speeds[i]+speeds[(i+1)%n]) for i,d in enumerate(ds))
    return speeds,seconds


def segment_clear(a,b,grid):
    count=max(1,math.ceil(math.dist(a,b)/(grid.res*.35)))
    return all(grid.clear((a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count))
               for i in range(count+1))


def validate_path(points,grid):
    LoopPath(points)
    if any(not segment_clear(a,points[(i+1)%len(points)],grid) for i,a in enumerate(points)):
        raise ValueError('PATH_SEGMENT_BLOCKED: correct map registration or the reference path')


def optimize(points,grid,profile,max_offset=.20,iterations=5):
    """Coordinate descent over smooth periodic lateral deformations, retaining start pose."""
    if not math.isfinite(max_offset) or not 0<max_offset<=.5 or not 1<=iterations<=30:
        raise ValueError('invalid optimization bounds')
    reference=[tuple(p) for p in points]
    validate_path(reference,grid)
    n=len(reference)
    if n<16: raise ValueError('resample reference to at least 16 points')
    normals=[]
    for i in range(n):
        a,b=reference[i-1],reference[(i+1)%n]
        d=math.dist(a,b)
        if d<1e-6: raise ValueError('ambiguous reference direction')
        normals.append((-(b[1]-a[1])/d,(b[0]-a[0])/d))
    offsets=[0.]*n
    def xy(values):
        return [(p[0]+v*norm[0],p[1]+v*norm[1]) for p,v,norm in zip(reference,values,normals)]
    _,baseline=trajectory(reference,profile)
    best=baseline; accepted=0
    # Overlapping smooth bumps keep numerical curvature stable at control boundaries.
    width=max(5,n//12)
    for sweep in range(iterations):
        step=max_offset/(2**(sweep+1))
        for center in range(3,n-3,max(2,width//3)):
            for direction in (-1,1):
                candidate=offsets[:]
                for i in range(max(3,center-width),min(n-3,center+width+1)):
                    weight=.5*(1+math.cos(math.pi*(i-center)/width))
                    candidate[i]=max(-max_offset,min(max_offset,candidate[i]+direction*step*weight))
                path=xy(candidate)
                try:
                    validate_path(path,grid)
                    _,cost=trajectory(path,profile)
                except ValueError:
                    continue
                if cost<best-1e-6:
                    offsets,best=candidate,cost
                    accepted+=1
    result=xy(offsets)
    validate_path(result,grid)
    velocities,estimate=trajectory(result,profile)
    return {'frame_id':'map','points':result,'speeds_mps':velocities,
            'optimization':{'method':'bounded smooth lateral coordinate descent',
                            'baseline_estimated_s':baseline,'optimized_estimated_s':estimate,
                            'improvement_percent':100*(baseline-estimate)/baseline,
                            'accepted_updates':accepted,'max_offset_m':max_offset,
                            'global_optimum_guaranteed':False}}
