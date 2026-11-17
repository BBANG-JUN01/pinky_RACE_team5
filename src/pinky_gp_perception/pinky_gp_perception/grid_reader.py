"""B/S05. 외부 ArUco/표식 pose 추정 결과에서 배정된 칸 하나만 선택.
코너 검출, 카메라 intrinsic/extrinsic, pose 좌표 변환은 adapter에서 구현.
"""
import math

def select_target(markers, assigned_id, now, max_age=.2):
    matches = [m for m in markers if m['id']==assigned_id]
    if len(matches)!=1: return None
    m=matches[0]
    if (not all(math.isfinite(v) for v in [now,m['captured_at'],*m['pose']])
        or len(m['pose'])!=3 or not 0<=now-m['captured_at']<=max_age): return None
    return {'grid_id':assigned_id,'pose':m['pose'],'valid':True}

def demo():
    return select_target([{'id':1,'pose':[.3,.01,.02],'captured_at':1.}],1,1.1)


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("perception/grid_reader", demo, args)


if __name__ == "__main__":
    main()
