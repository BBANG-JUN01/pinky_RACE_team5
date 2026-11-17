"""ROS-independent policy primitives. Not a complete motion controller."""
from dataclasses import dataclass, field
from enum import Enum
import math

class Restriction(str, Enum):
    NORMAL = 'NORMAL'
    YELLOW = 'YELLOW'
    SC = 'SC'

@dataclass
class RacePolicy:
    race_id: str
    aborted: bool = False
    restriction: Restriction = Restriction.NORMAL
    restriction_since: float = float('-inf')
    last_signal_at: float = float('-inf')
    seen: set = field(default_factory=set)

    def signals(self, events):
        """Process one batch; caller must validate capture time/freshness/source.
        Events: (race_id, command_id, kind, timestamp). RED dominates its batch.
        """
        fresh = []
        for race_id, command_id, kind, at in events:
            if race_id != self.race_id or command_id in self.seen or not math.isfinite(at):
                continue
            if kind not in {'RED', 'YELLOW', 'GREEN', 'SC_ON'}:
                continue
            self.seen.add(command_id)
            fresh.append((kind, at))
        if any(kind == 'RED' for kind, _ in fresh):
            self.aborted = True
            return
        if self.aborted:
            return
        # At equal times restrictions override green; SC wins over yellow.
        priority = {'GREEN': 0, 'YELLOW': 1, 'SC_ON': 2}
        for kind, at in sorted(fresh, key=lambda e: (e[1], priority[e[0]])):
            if at < self.last_signal_at:
                continue
            if kind == 'GREEN':
                if at <= self.restriction_since:
                    continue
                self.restriction = Restriction.NORMAL
            elif kind == 'SC_ON':
                self.restriction = Restriction.SC
                self.restriction_since = at
            elif kind == 'YELLOW':
                if self.restriction != Restriction.SC:
                    self.restriction = Restriction.YELLOW
                self.restriction_since = max(self.restriction_since, at)
            self.last_signal_at = max(self.last_signal_at, at)

@dataclass
class StopReasons:
    reasons: set = field(default_factory=set)
    def set(self, source, active):
        if active:
            self.reasons.add(source)
        else:
            self.reasons.discard(source)
    @property
    def stopped(self):
        return bool(self.reasons)

@dataclass
class Penalty:
    duration_s: float
    stopped_since: float | None = None
    elapsed_s: float = 0.0
    complete: bool = False

    def __post_init__(self):
        if not math.isfinite(self.duration_s) or self.duration_s <= 0:
            raise ValueError('duration must be positive and finite')

    def update(self, now, measured_stopped):
        """now must be local monotonic time; motion resets continuous stop time."""
        if not math.isfinite(now):
            raise ValueError('invalid clock')
        if self.complete:
            return 0.0
        if not measured_stopped:
            self.stopped_since = None
            self.elapsed_s = 0.0
        elif self.stopped_since is None or now < self.stopped_since:
            self.stopped_since = now
            self.elapsed_s = 0.0
        else:
            self.elapsed_s = now - self.stopped_since
        self.complete = self.elapsed_s >= self.duration_s
        return max(0.0, self.duration_s - self.elapsed_s)

def effective_speed(base, hardware, local_cap, race, stops, drs_requested=False,
                    drs_cap=None, zone=False, data_fresh=False, clearance=False):
    """Returns (cap, drs_active). Guard's sensor freshness must also be checked."""
    values = [base, hardware, local_cap]
    if any(not math.isfinite(v) or v < 0 for v in values):
        return 0.0, False
    if race.aborted or stops.stopped or not data_fresh:
        return 0.0, False
    # Yellow/SC caps must already be included in local_cap by the ROS adapter.
    eligible = (race.restriction == Restriction.NORMAL and drs_requested and zone
                and clearance and drs_cap is not None and math.isfinite(drs_cap)
                and drs_cap > base)
    requested = drs_cap if eligible else base
    cap = min(requested, hardware, local_cap)
    return cap, bool(eligible and cap > base)

def drs_gap(ego_s, other_s, length, same_lap, same_direction, valid, threshold):
    vals = [ego_s, other_s, length, threshold]
    if any(not math.isfinite(v) for v in vals) or length <= 0 or threshold <= 0:
        return False
    if not (same_lap and same_direction and valid):
        return False
    if not (0 <= ego_s < length and 0 <= other_s < length):
        return False
    # Same lap: a trailing car across the finish must not become an opponent ahead.
    delta = other_s - ego_s
    return 0 < delta <= threshold
