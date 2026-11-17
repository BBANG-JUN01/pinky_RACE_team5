"""C/S09. 추월 FSM 가이드. 공간 검사는 호출자가 전체 후보/합류 경로에 수행.
ABORT는 원래 경로 강제 복귀가 아니다. 정지 후 안전 재계획과 새 시도 필요.
SC 순서 고정/앞차 추종은 별도 progress+speed 정책에서 처리한다.
"""
class OvertakeManager:
    def __init__(self): self.state='FOLLOW'
    def update(self, requested=False, zone=False, restriction='NORMAL', candidate_clear=False,
               merge_clear=False, ahead=False, on_baseline=False, stopped=False, fault=False):
        allowed=zone and restriction=='NORMAL' and not fault
        if self.state in {'CHECK','PASS','MERGE'} and not allowed:
            self.state='ABORT'
        elif self.state=='FOLLOW' and requested and allowed: self.state='CHECK'
        elif self.state=='CHECK' and candidate_clear and merge_clear: self.state='PASS'
        elif self.state=='PASS':
            if not candidate_clear: self.state='ABORT'
            elif ahead and merge_clear: self.state='MERGE'
        elif self.state=='MERGE':
            if not merge_clear: self.state='ABORT'
            elif on_baseline: self.state='FOLLOW'
        elif self.state=='ABORT' and stopped and not fault: self.state='FOLLOW'
        return self.state

def demo():
    o=OvertakeManager()
    return [o.update(requested=True,zone=True),
            o.update(zone=True,candidate_clear=True,merge_clear=True),
            o.update(restriction='SC')]


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("behavior/behavior_manager", demo, args)


if __name__ == "__main__":
    main()
