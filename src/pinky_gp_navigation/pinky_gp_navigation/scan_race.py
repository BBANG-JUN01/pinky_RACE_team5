"""Closed-loop race control with map clearance and live scan collision checks (SI)."""
import math
from bisect import bisect_right
from dataclasses import dataclass
from functools import lru_cache
from pinky_gp_core.policy import Penalty, RacePolicy
from pinky_gp_core.timing import LapTimer
from .hardware_limits import Limits, speed_profile
from .pure_pursuit import PurePursuit, pursuit_curvature

# Simulation profile only. Hardware launch has an independent measured-limit gate.
SIM_LIMITS = Limits(speed=.24, braking=.60, latency=.23, margin=.03, lateral_accel=.32, angular=1.65)
RADIUS = .13
LOOKAHEAD = .26
HORIZON = .74


@lru_cache(maxsize=8)
def disk(resolution, radius):
    r = math.ceil(radius / resolution + 1)
    return tuple((dx, dy) for dx in range(-r, r+1) for dy in range(-r, r+1)
                 if math.hypot(dx, dy)*resolution <= radius + resolution*math.sqrt(2))


class Occupancy:
    def __init__(self, width, height, resolution, origin, data, radius=RADIUS):
        if (width < 1 or height < 1 or len(data) != width*height or len(origin) != 2
                or not all(math.isfinite(v) for v in (*origin, resolution, radius))
                or resolution <= 0 or radius <= 0):
            raise ValueError('INVALID_MAP')
        self.res, self.origin, self.radius = resolution, origin, radius
        self.width, self.height = width, height
        self.offsets = disk(resolution, radius)
        self.occupied = set()
        self.static = set()
        for i, value in enumerate(data):
            if value < 0 or value >= 50:
                cell = i % width, i // width
                self.occupied.add(cell)
                self.inflate(self.static, cell)

    def cell(self, x, y):
        return (math.floor((x-self.origin[0])/self.res), math.floor((y-self.origin[1])/self.res))

    def inflate(self, cells, point):
        x, y = point
        cells.update((x+dx, y+dy) for dx, dy in self.offsets)

    def clear(self, point, live):
        x, y = self.cell(*point)
        border = math.ceil(self.radius/self.res)
        return (border <= x < self.width-border and border <= y < self.height-border
                and (x, y) not in self.static and (x, y) not in live)


def scan_points(ranges, first, step, low, high, laser_pose):
    """Transform a full scan at acquisition time; require evidence in every octant."""
    geometry = (first, step, low, high, *laser_pose)
    if (not all(math.isfinite(v) for v in geometry) or len(ranges) < 32 or step == 0
            or not 0 < low < high or abs(step)*(len(ranges)-1) < 2*math.pi-.15):
        raise ValueError('INVALID_SCAN')
    seen = [0]*8
    hits = []
    finite_octants = set()
    lx, ly, heading = laser_pose
    for i, d in enumerate(ranges):
        if not ((math.isfinite(d) and low <= d <= high) or d == math.inf):
            continue
        a = first+i*step+heading
        seen[int((a % (2*math.pi))*4/math.pi) % 8] += 1
        if math.isfinite(d):
            finite_octants.add(int((a % (2*math.pi))*4/math.pi) % 8)
            if d <= HORIZON + .65:
                hits.append((lx+d*math.cos(a), ly+d*math.sin(a)))
    if len(finite_octants) < 8 or min(seen) < max(2, len(ranges)//24):
        raise ValueError('BLIND_SCAN')
    return hits


@dataclass(frozen=True)
class Drive:
    v: float = 0.
    w: float = 0.
    reason: str = 'READY'
    error: float = 0.


class RaceDrive:
    def __init__(self, points, grid, laps=3, limits=SIM_LIMITS, race_id='sim'):
        if type(laps) is not int or laps < 1:
            raise ValueError('INVALID_LAPS')
        self.tracker = PurePursuit(points, LOOKAHEAD, limits.speed, limits.angular, .45)
        self.path = self.tracker.path
        self.caps = speed_profile(points, limits)
        self.grid, self.limit, self.goal = grid, limits, laps
        self.timer = LapTimer(('Q1','Q2','Q3','LINE'))
        self.policy = RacePolicy(race_id)
        self.penalty = None
        self.people = False
        self.events = set()
        self.finish_at_line = False
        self.done = False
        self.fault = ''
        self.previous = None
        self.previous_pose = None
        self.person_stamp = -math.inf
        self.last_at = None
        self.offset = 0.
        self.clear_frames = 0
        self.lane_start = None
        self.lane_start_offset = 0.

    def event(self, kind, ident, at, duration=0.):
        if not ident or ident in self.events or not math.isfinite(at) or self.done or self.policy.aborted:
            return False
        if kind in ('RED','YELLOW','GREEN','SC_ON'):
            self.policy.signals([(self.policy.race_id, ident, kind, at)])
        elif kind == 'CHECKER':
            self.finish_at_line = True
        elif kind in ('PERSON_ON','PERSON_OFF'):
            if at < self.person_stamp or (at == self.person_stamp and kind == 'PERSON_OFF'):
                return False
            self.person_stamp = at
            self.people = kind == 'PERSON_ON'
        elif kind == 'PENALTY' and self.penalty is None and 0 < duration <= 60 and math.isfinite(duration):
            self.penalty = Penalty(duration)
        else:
            return False
        self.events.add(ident)
        return True

    def sample(self, s, offset):
        s %= self.path.length
        i = bisect_right(self.path.starts, s)-1
        a = self.path.points[i]
        b = self.path.points[(i+1) % len(self.path.points)]
        ux = (b[0]-a[0])/self.path.lengths[i]
        uy = (b[1]-a[1])/self.path.lengths[i]
        t = s-self.path.starts[i]
        return a[0]+t*ux-offset*uy, a[1]+t*uy+offset*ux

    def target(self, s, d, lateral, lane):
        # Keep the accepted lane-change curve anchored while the robot moves along it.
        if lane == self.offset and self.lane_start is not None:
            travel = (s-self.lane_start) % self.path.length
            if travel < self.path.length/2:
                d_along = d+travel
                lateral = self.lane_start_offset
            else:
                d_along = d
        else:
            d_along = d
        t = min(1., d_along/.30)
        blend = t*t*(3.-2.*t)
        return self.sample(s+d, lateral+(lane-lateral)*blend)

    def lane_clear(self, s, lateral, lane, live):
        return all(self.grid.clear(self.target(s, i*HORIZON/28, lateral, lane),live)
                   for i in range(1,29))

    def time_gates(self, s, now):
        if self.previous is None:
            if min(s,self.path.length-s) > .14:
                raise ValueError('START_OUTSIDE_GRID')
            self.timer.start(now)
        else:
            length = self.path.length
            ds = (s-self.previous+length/2) % length-length/2
            if abs(ds) > min(length/8, .055+self.limit.speed*1.6*(now-self.last_at)):
                raise ValueError('LOCALIZATION_JUMP')
            if ds > 0:
                # Signed forward crossing and ordered gates reject reverse/finish jitter.
                for i, gate in enumerate(self.timer.gates,1):
                    advance = (i*length/4-self.previous) % length
                    if 1e-9 < advance <= ds+1e-9:
                        event_time = self.last_at+(now-self.last_at)*min(1.,advance/ds)
                        counted = self.timer.gate(gate,event_time)
                        if counted and gate == 'LINE' and (self.finish_at_line or len(self.timer.laps)>=self.goal):
                            self.done = True
                            self.timer.freeze(event_time)
        self.previous, self.last_at = s, now

    def step(self, pose, hits, now, measured_v, measured_w):
        if self.policy.aborted: return Drive(reason='RED')
        if self.done: return Drive(reason='FINISHED')
        if self.fault: return Drive(reason=self.fault)
        if not all(math.isfinite(v) for v in (*pose,now,measured_v,measured_w)):
            return Drive(reason='INVALID_INPUT')
        if self.last_at is not None and now <= self.last_at:
            return Drive(reason='OLD_SAMPLE')
        x,y,yaw = pose
        try:
            if self.previous_pose is not None:
                dt = now-self.last_at
                if math.dist(self.previous_pose, (x,y)) > .065+self.limit.speed*1.8*min(dt,.4):
                    raise ValueError('LOCALIZATION_JUMP')
                if self.penalty and dt>.35:
                    self.penalty.update(now,False)
            p = self.path.project((x,y),self.tracker.segment,window=8,max_error=.44)
            self.tracker.segment = p['segment']
            self.time_gates(p['s'],now)
            self.previous_pose = x,y
        except ValueError as exc:
            self.fault = str(exc)
            return Drive(reason=self.fault)
        if self.done: return Drive(reason='FINISHED')
        if self.penalty:
            self.penalty.update(now,abs(measured_v)<.012 and abs(measured_w)<.06)
            if self.penalty.complete:
                self.penalty = None
            else:
                return Drive(reason='PENALTY')
        if self.people: return Drive(reason='PERSON')
        # Cache unique laser cells. The static map remains immutable during the race.
        live = set()
        for cell in {self.grid.cell(px,py) for px,py in hits if math.hypot(px-x,py-y)<HORIZON+.50}:
            if cell not in self.grid.occupied:
                self.grid.inflate(live,cell)
        s = p['s']
        cx,cy = self.sample(s,0.)
        nx,ny = self.sample(s,1.)
        lateral = (x-cx)*(nx-cx)+(y-cy)*(ny-cy)
        if not self.grid.clear((x,y),live):
            return Drive(reason='FOOTPRINT_BLOCKED',error=p['error'])
        center_clear = self.lane_clear(s,lateral,0.,live)
        self.clear_frames = min(4,self.clear_frames+1) if center_clear else 0
        preferred = 0. if self.clear_frames>=4 else self.offset
        side = 1. if self.offset >= 0 else -1.
        for lane in dict.fromkeys([preferred,self.offset,0.,side*.245,side*.26,-side*.245,-side*.26]):
            if self.lane_clear(s,lateral,lane,live):
                if lane != self.offset:
                    self.lane_start,self.lane_start_offset = s,lateral
                self.offset = lane
                break
        else:
            return Drive(reason='NO_CLEAR_LANE',error=p['error'])
        tx,ty = self.target(s,.16 if self.offset else LOOKAHEAD,lateral,self.offset)
        try:
            k = pursuit_curvature(x,y,yaw,tx,ty)
        except ValueError:
            self.fault = 'WRONG_HEADING'
            return Drive(reason=self.fault)
        idx = p['segment']
        cap = min(self.caps[idx],self.caps[(idx+1)%len(self.caps)],self.limit.corner_cap(k))
        cap = min(cap, {'NORMAL':self.limit.speed,'YELLOW':.12,'SC':.09}[self.policy.restriction.value])
        if self.offset: cap = min(cap,.16)
        # Check the actual commanded arc for at least the current stopping distance.
        speed = max(cap,abs(measured_v))
        required = self.limit.margin+speed*self.limit.latency+speed**2/(2*self.limit.braking)
        for j in range(1,math.ceil(required/.02)+1):
            d = min(j*.02,required)
            ax,ay = (d,0.) if abs(k)<1e-7 else (math.sin(k*d)/k,(1-math.cos(k*d))/k)
            arc = (x+math.cos(yaw)*ax-math.sin(yaw)*ay,y+math.sin(yaw)*ax+math.cos(yaw)*ay)
            if not self.grid.clear(arc,live):
                return Drive(reason='BRAKING_ARC_BLOCKED',error=p['error'])
        return Drive(cap,cap*k,'BYPASS' if self.offset else 'TRACKING',p['error'])
