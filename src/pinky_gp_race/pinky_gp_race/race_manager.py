"""C/S05-S07. 명시적 조건을 확인하는 생애 FSM, RED terminal.
조건 evidence는 adapter가 실제 관측으로 생성해야 한다. 운영자 버튼만으로 True 금지.
새 경기 RESET은 새 인스턴스/새 race_id로 수행하며 ESTOP 해제와 분리한다.
"""
from pinky_gp_core.policy import RacePolicy

class RaceManager:
    TRANSITIONS = {
        'CHECK':('IDLE','CHECKING',('healthy',)),
        'MAP_READY':('CHECKING','MAP_READY',('guard_ready','map_valid','path_valid','shared')),
        'GRID':('MAP_READY','GRID_ALIGN',('localized',)),
        'ARM_START':('GRID_ALIGN','STARTING',('both_ready',)),
        'START':('STARTING','RACING',('both_ready','lights_valid','healthy')),
        'CHECKER':('RACING','FINISHING',()),
        'FINISH':('FINISHING','FINISHED',('all_finished','all_stopped')),
    }
    def __init__(self, race_id):
        if not race_id: raise ValueError('race_id required')
        self.policy=RacePolicy(race_id); self.phase='IDLE'; self.results={}

    def command(self, race_id, command_id, kind, evidence=None):
        if race_id!=self.policy.race_id or not command_id: return False
        if command_id in self.results: return self.results[command_id]
        evidence=evidence or {}
        accepted=False
        if kind=='RED' and self.phase!='FINISHED':
            self.phase='ABORTED'; self.policy.aborted=True; accepted=True
        elif self.phase not in {'ABORTED','FINISHED'} and kind in self.TRANSITIONS:
            before,after,requirements=self.TRANSITIONS[kind]
            if self.phase==before and all(evidence.get(k) is True for k in requirements):
                self.phase=after; accepted=True
        self.results[command_id]=accepted
        return accepted

    def signals(self, events):
        if self.phase == 'FINISHED': return
        self.policy.signals(events)
        if self.policy.aborted and self.phase!='FINISHED': self.phase='ABORTED'

def demo():
    r=RaceManager('demo')
    r.command('demo','1','CHECK',{'healthy':True})
    r.command('demo','2','RED')
    r.signals([('demo','3','GREEN',2.)])
    return {'phase':r.phase,'aborted':r.policy.aborted}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("race/race_manager", demo, args)


if __name__ == "__main__":
    main()

