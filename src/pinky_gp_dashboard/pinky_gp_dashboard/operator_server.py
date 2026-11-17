"""D/S05-S08. 관제 명령 생성 계약. HTTP 서버/인증/ROS 서비스는 미연결.
운영 UI는 여기서 생성한 command_id를 재전송에도 유지한다.
accepted와 실제 완료를 구분해서 표시하고 모든 요청/결과를 JSONL로 기록한다.
"""
from dataclasses import dataclass,asdict
import math
import uuid

@dataclass(frozen=True)
class OperatorCommand:
    race_id: str
    command_id: str
    kind: str
    issued_at: float
    robot: str | None = None
    duration: float | None = None

    @classmethod
    def build(cls,race_id,kind,issued_at,robot=None,duration=None):
        allowed={'CHECK','RECON','GRID','ARM_START','CHECKER','RED','YELLOW','GREEN','SC_ON','PENALTY'}
        if not race_id or kind not in allowed or not math.isfinite(issued_at):
            raise ValueError('invalid command')
        if kind=='PENALTY' and (robot not in {'A','B'} or duration is None or not math.isfinite(duration) or duration<=0):
            raise ValueError('penalty requires robot and positive duration')
        return cls(race_id,str(uuid.uuid4()),kind,issued_at,robot,duration)

def demo():
    return asdict(OperatorCommand.build('demo','PENALTY',1.,'A',3.))


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("dashboard/operator_server", demo, args)


if __name__ == "__main__":
    main()
