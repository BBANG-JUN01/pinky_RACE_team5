"""ROS-independent command arbitration. All times are local monotonic seconds."""
from math import isfinite

class CommandGuard:
    def __init__(self, linear_limit, angular_limit, timeout, required=('scan', 'heartbeat')):
        if not all(isfinite(v) and v > 0 for v in (linear_limit, angular_limit, timeout)):
            raise ValueError('limits and timeout must be finite and positive')
        self.limits = linear_limit, angular_limit
        self.timeout = timeout
        self.required = tuple(required)
        self.source = None
        self.command = None
        self.health = {}
        self.stops = set()
        self.last_tick = None

    def select(self, source):
        # Re-selection also invalidates the old command.
        self.source = source
        self.command = None

    def observe(self, name, now):
        if not isfinite(now):
            raise ValueError('invalid time')
        self.health[name] = now

    def receive(self, source, linear, angular, now):
        if source != self.source or source is None:
            return False
        if not all(isfinite(v) for v in (linear, angular, now)):
            self.command = None
            return False
        self.command = (linear, angular, now)
        return True

    def stop(self, reason, active=True):
        if not reason:
            raise ValueError('empty reason')
        if active:
            self.stops.add(reason)
            self.command = None
        else:
            self.stops.discard(reason)

    def tick(self, now):
        if not isfinite(now):
            return 0., 0., ('INVALID_CLOCK',)
        if self.last_tick is not None and now < self.last_tick:
            self.command = None
            self.health.clear()
        self.last_tick = now
        reasons = set(self.stops)
        for name in self.required:
            age = now - self.health.get(name, float('-inf'))
            if not 0 <= age <= self.timeout:
                reasons.add('STALE_' + name)
        if self.command is None or not 0 <= now-self.command[2] <= self.timeout:
            reasons.add('STALE_COMMAND')
        if reasons:
            self.command = None
            return 0., 0., tuple(sorted(reasons))
        v, w, _ = self.command
        # Forward only. Uniform scaling preserves requested curvature.
        if v < 0:
            self.command = None
            return 0., 0., ('REVERSE_DISABLED',)
        scale = min(1., self.limits[0]/v if v else 1., self.limits[1]/abs(w) if w else 1.)
        return v*scale, w*scale, ()
