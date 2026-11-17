"""C/S08. 로봇별 연속 정지 계시와 중복 ID 배제.
실제 odom 선속도/각속도가 모두 허용치 이하이고 fresh일 때만 stopped=True로 입력.
해제 출력은 PENALTY 사유에만 적용하며 PERSON/RED/ESTOP는 유지한다.
"""
from pinky_gp_core.policy import Penalty

class PenaltyManager:
    def __init__(self): self.active={}; self.seen=set()
    def issue(self, command_id, robot, duration):
        if not command_id or command_id in self.seen or robot in self.active: return False
        penalty=Penalty(duration)
        self.seen.add(command_id); self.active[robot]=penalty; return True
    def update(self, robot, now, measured_stopped, odom_fresh):
        if robot not in self.active: return {'remaining':0.,'stop':False}
        p=self.active[robot]; remaining=p.update(now, measured_stopped and odom_fresh)
        if p.complete: del self.active[robot]
        return {'remaining':remaining,'stop':not p.complete}

def demo():
    p=PenaltyManager();p.issue('penalty-1','A',2.)
    return [p.update('A',t,True,True) for t in (0.,1.,2.)]


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("race/penalty_manager", demo, args)


if __name__ == "__main__":
    main()
