"""A/S05. 순차 접근 후 마커 상대 오차 기반 저속 정렬 예제.
목표를 로봇 base frame으로 변환한 x/y(m), yaw(rad)를 전달한다.
상대 로봇 점유·표식 유실 시 정지. READY는 정지 관측과 연속 허용오차가 필요하다.
"""
import math

class GridAligner:
    def __init__(self, stable_frames=3):
        if stable_frames < 1: raise ValueError('invalid stable_frames')
        self.required = stable_frames; self.stable = 0

    def update(self, x, y, yaw, fresh, clear, measured_stopped):
        if not fresh or not clear or not all(math.isfinite(v) for v in (x,y,yaw)):
            self.stable = 0
            return (0.,0.,'WAIT_VALID_TARGET')
        if abs(x) < .03 and abs(y) < .03 and abs(yaw) < .08:
            self.stable = self.stable+1 if measured_stopped else 0
            return (0.,0.,'READY' if self.stable >= self.required else 'SETTLING')
        self.stable = 0
        if x < -.03:
            return (0.,0.,'REPLAN_APPROACH')
        if abs(x) < .03 and abs(y) >= .03:
            return (0.,0.,'REPLAN_APPROACH')
        bearing = math.atan2(y,x) if math.hypot(x,y) >= .03 else yaw
        return (min(.06,max(0.,x*.4)) if abs(bearing)<.4 else 0.,
                max(-.3,min(.3,bearing)), 'ALIGN')

def demo():
    g = GridAligner()
    return [g.update(.01,.01,.01,True,True,True) for _ in range(3)]


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("navigation/grid_manager", demo, args)


if __name__ == "__main__":
    main()
