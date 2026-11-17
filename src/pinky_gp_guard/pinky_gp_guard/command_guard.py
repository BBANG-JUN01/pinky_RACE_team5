"""D/S01. 제어권·신선도·정지 사유를 통과한 후보만 반환하는 순수 로직.
출력은 (linear m/s, angular rad/s, reason). 실제 base 토픽 발행은 미연결.
하드웨어 adapter에서 이 함수 결과만 발행하고 base 자체 watchdog도 검증한다.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Velocity:
    source: str
    linear: float
    angular: float
    received_at: float

class CommandGuard:
    SOURCES = {'RECON': 'recon', 'GRID_ALIGN': 'grid', 'RACING': 'nav', 'FINISHING': 'nav'}

    def __init__(self, max_linear=.15, max_angular=.6, timeout=.25):
        if any(not math.isfinite(x) or x <= 0 for x in (max_linear, max_angular, timeout)):
            raise ValueError('invalid limits')
        self.max_linear, self.max_angular, self.timeout = max_linear, max_angular, timeout

    def evaluate(self, command, now, phase, stops=(), health_faults=(), enabled=False):
        if not enabled or stops or health_faults:
            return 0., 0., 'DISABLED_OR_STOP'
        if command is None or phase not in self.SOURCES or command.source != self.SOURCES[phase]:
            return 0., 0., 'NO_CONTROL_AUTHORITY'
        if any(not math.isfinite(x) for x in (command.linear, command.angular, command.received_at, now)):
            return 0., 0., 'INVALID_COMMAND'
        if not 0 <= now-command.received_at <= self.timeout:
            return 0., 0., 'COMMAND_TIMEOUT'
        if command.linear < 0:
            return 0., 0., 'REVERSE_NOT_ALLOWED'
        # 동일 비율로 축소해 후보의 곡률을 보존한다.
        scale = min(1., self.max_linear/max(command.linear, 1e-9),
                    self.max_angular/max(abs(command.angular), 1e-9))
        return command.linear*scale, command.angular*scale, 'OK'

def demo():
    guard = CommandGuard()
    cmd = Velocity('nav', .3, .2, 1.)
    return {'accepted': guard.evaluate(cmd, 1.1, 'RACING', enabled=True),
            'timeout': guard.evaluate(cmd, 2., 'RACING', enabled=True)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("guard/command_guard", demo, args)


if __name__ == "__main__":
    main()
