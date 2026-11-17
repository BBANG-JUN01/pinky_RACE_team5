"""A/S02. 시작 구역 이탈·최소 이동·진행 방향·표식 재관측으로 복귀 판정.
SLAM 시작/저장 서비스는 외부 adapter에서 호출. RETURNED는 MAP_READY가 아니다.
"""
from dataclasses import dataclass
import math

@dataclass
class ReconManager:
    min_distance: float = 3.
    timeout: float = 120.
    started_at: float | None = None
    left_start: bool = False
    state: str = 'IDLE'

    def start(self, now):
        if self.state != 'IDLE' or not math.isfinite(now):
            raise ValueError('invalid recon start')
        self.started_at, self.state = now, 'RECON'

    def update(self, now, distance, in_start, marker_visible, same_direction, healthy):
        if self.state != 'RECON':
            return self.state
        if (not healthy or not math.isfinite(now) or not math.isfinite(distance)
            or distance < 0 or not 0 <= now-self.started_at <= self.timeout):
            self.state = 'FAILED'
        else:
            self.left_start |= not in_start
            if self.left_start and distance >= self.min_distance and in_start and marker_visible and same_direction:
                self.state = 'RETURNED'
        return self.state

def demo():
    r = ReconManager(); r.start(0.)
    early = r.update(1., .1, True, True, True, True)
    r.update(2., 1., False, False, True, True)
    return {'early': early, 'returned': r.update(10., 4., True, True, True, True)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("recon/recon_manager", demo, args)


if __name__ == "__main__":
    main()
