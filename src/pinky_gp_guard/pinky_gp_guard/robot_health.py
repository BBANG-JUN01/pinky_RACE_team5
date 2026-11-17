"""D/S00-S01. 각 입력의 수신 시각을 같은 로컬 monotonic clock으로 관리.
ROS 연결: scan/odom/vision/중앙 heartbeat callback에서 touch(), timer에서 faults().
촬영 stamp의 시간 동기화/역행/중복 검사는 callback의 별도 책임이다.
"""
from dataclasses import dataclass, field
import math

@dataclass
class HealthMonitor:
    deadlines: dict
    received: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.deadlines or any(not math.isfinite(v) or v <= 0 for v in self.deadlines.values()):
            raise ValueError('positive deadlines required')

    def touch(self, source, now):
        if source not in self.deadlines or not math.isfinite(now):
            raise ValueError('unknown source or invalid clock')
        if source in self.received and now <= self.received[source]:
            raise ValueError('clock must advance')
        self.received[source] = now

    def faults(self, now):
        return sorted(name for name, limit in self.deadlines.items()
                      if not math.isfinite(now) or name not in self.received
                      or not 0 <= now - self.received[name] <= limit)

def demo():
    health = HealthMonitor({'scan': .3, 'heartbeat': .5})
    health.touch('scan', 1.)
    return {'missing': health.faults(1.1), 'expired': health.faults(2.)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("guard/robot_health", demo, args)


if __name__ == "__main__":
    main()
