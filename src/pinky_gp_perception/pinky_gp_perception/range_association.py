"""B/S06. 보정 완료한 카메라 ROI에 투영된 LiDAR 후보 거리의 보수적 연관 예제.
입력은 양 센서 시간 동기화 후 ROI에 투영한 거리들이다. TF/투영 자체는 미구현.
서로 다른 깊이 군집이 섞이면 invalid. 단안 박스 크기로 거리를 추측하지 않는다.
"""
import math
from statistics import median

def associate(ranges, image_at, scan_at, calibrated=False, max_skew=.08, spread=.2):
    invalid = {'valid':False,'distance':None}
    if (not calibrated or not all(math.isfinite(x) for x in (image_at,scan_at))
        or abs(image_at-scan_at)>max_skew): return invalid
    valid = [x for x in ranges if math.isfinite(x) and x>0]
    if len(valid)<3 or max(valid)-min(valid)>spread: return invalid
    return {'valid':True,'distance':median(valid)}

def demo():
    return {'valid':associate([1.,1.02,1.01],1.,1.01,True),
            'ambiguous':associate([.5,1.,2.],1.,1.,True)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("perception/range_association", demo, args)


if __name__ == "__main__":
    main()
