"""C/S05. 검증된 checkpoint 이벤트를 LapTimer에 전달하고 순위 계산.
pose -> gate 교차, 방향, teleport 거부는 외부 측정 adapter 책임. 수신 시각으로 재계시 금지.
"""
from pinky_gp_core.timing import LapTimer
import math

class ProgressManager:
    def __init__(self, robot_ids=('A','B'), gates=('CP1','CP2','FINISH')):
        self.timers={r:LapTimer(gates) for r in robot_ids}; self.finished=set(); self.checker=False

    def start(self, at):
        for timer in self.timers.values(): timer.start(at)

    def gate(self, robot, name, at, forward=True):
        t=self.timers[robot]; before=len(t.laps)
        accepted=t.gate(name,at,forward)
        if accepted and len(t.laps)>before and self.checker:
            t.freeze(at); self.finished.add(robot)
        return accepted

    def abort(self, at):
        for timer in self.timers.values():
            if timer.start_at is not None and timer.frozen_at is None: timer.freeze(at)

    def snapshot(self, robot, now):
        t=self.timers[robot]
        return {'robot':robot,'completed_laps':len(t.laps),'current':t.current(now),
                'last':t.last,'best':t.best,'finished':robot in self.finished}

def ranking(progress, length):
    """progress={robot:(completed_laps,s)}. 동점은 같은 순위, 로봇 ID는 표시 순서만 결정."""
    if not math.isfinite(length) or length<=0: raise ValueError('invalid track')
    values={}
    for r,(lap,s) in progress.items():
        if not isinstance(lap,int) or lap<0 or not math.isfinite(s) or not 0<=s<length:
            raise ValueError('invalid progress')
        values[r]=lap*length+s
    return {r:1+sum(v>value for v in values.values()) for r,value in values.items()}

def demo():
    p=ProgressManager();p.start(0.)
    for gate,at in [('CP1',2.),('CP2',4.),('FINISH',6.)]: p.gate('A',gate,at)
    return p.snapshot('A',7.)


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("race/progress_manager", demo, args)


if __name__ == "__main__":
    main()
