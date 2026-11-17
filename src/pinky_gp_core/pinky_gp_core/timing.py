"""Caller supplies monotonic seconds and validated, ordered checkpoint events."""
from dataclasses import dataclass, field
import math

@dataclass
class LapTimer:
    gates: tuple
    start_at: float | None = None
    lap_start: float | None = None
    next_index: int = 0
    laps: list = field(default_factory=list)
    frozen_at: float | None = None
    last_event_at: float = float('-inf')

    def __post_init__(self):
        if len(self.gates) < 2 or len(set(self.gates)) != len(self.gates):
            raise ValueError('need unique ordered checkpoints ending in finish')

    def start(self, at):
        if self.start_at is not None or not math.isfinite(at):
            raise ValueError('invalid start')
        self.start_at = self.lap_start = at
        self.last_event_at = at

    def gate(self, name, at, forward=True):
        if (self.start_at is None or self.frozen_at is not None or not forward
            or not math.isfinite(at) or at <= self.last_event_at
            or name != self.gates[self.next_index]):
            return False
        self.last_event_at = at
        self.next_index += 1
        if self.next_index == len(self.gates):
            self.laps.append(at - self.lap_start)
            self.lap_start = at
            self.next_index = 0
        return True

    def freeze(self, at):
        if self.start_at is None or not math.isfinite(at) or at < self.last_event_at:
            raise ValueError('invalid freeze')
        if self.frozen_at is None:
            self.frozen_at = at

    def current(self, now):
        if self.lap_start is None:
            return 0.0
        if not math.isfinite(now):
            raise ValueError('invalid time')
        return max(0.0, (self.frozen_at if self.frozen_at is not None else now)-self.lap_start)

    @property
    def last(self):
        return self.laps[-1] if self.laps else None

    @property
    def best(self):
        return min(self.laps) if self.laps else None
