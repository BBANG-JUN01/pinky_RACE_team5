"""B/S05-S07. 출발등 1..N 순차 점등 후 안정된 0 관측만 승인.
ROI 유실/영상 stale/순서 오류는 시퀀스를 취소. 깃발 RED/GREEN은 별도 RacePolicy 사용.
동일 프레임 중복을 거부하고 다음 경기에는 새 인스턴스를 사용한다.
"""
import math

class StartLights:
    def __init__(self, lights=5, stable_frames=2):
        if lights<1 or stable_frames<1: raise ValueError('invalid sequence')
        self.lights=lights; self.required=stable_frames
        self.level=0; self.candidate=None; self.count=0
        self.last_at=float('-inf'); self.triggered=False

    def observe(self, count, at, roi_visible=True, fresh=True):
        if self.triggered: return False
        if not math.isfinite(at) or at<=self.last_at: return False
        self.last_at=at
        if not roi_visible or not fresh or count not in range(self.lights+1):
            self.level=0; self.count=0; self.candidate=None; return False
        self.count=self.count+1 if count==self.candidate else 1
        self.candidate=count
        if self.count<self.required: return False
        if count==0 and self.level==self.lights:
            self.triggered=True; return True
        if count==self.level+1:
            self.level=count
        elif count!=self.level:
            self.level=0
        return False

def demo():
    s=StartLights(lights=3)
    return [s.observe(c,float(i)) for i,c in enumerate([1,1,2,2,3,3,0,0])]


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("perception/signal_reader", demo, args)


if __name__ == "__main__":
    main()
