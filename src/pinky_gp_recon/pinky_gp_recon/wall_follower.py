"""A/S02. 왼쪽 벽 추종 P 제어 기준 예제. 실제 조향 튜닝 전 저속 bag 재생용.
입력은 base frame 기준 전방/좌측 유효 거리. LaserScan 각도 영역 추출은 adapter 책임.
후속: 양쪽 벽 선택, PID 적분 anti-windup, 코너 탈출, scan timestamp 검증.
"""
import math
from statistics import median

def sector_distance(ranges, range_min, range_max):
    values = [x for x in ranges if math.isfinite(x) and range_min <= x <= range_max]
    return median(values) if values else None

def wall_command(front, left, target=.30, speed=.10, kp=1.2, stop_distance=.25):
    vals = (front, left, target, speed, kp, stop_distance)
    if any(x is None or not math.isfinite(x) or x <= 0 for x in vals):
        return (0., 0., 'INVALID_SCAN')
    if front <= stop_distance:
        return (0., 0., 'FRONT_BLOCKED')
    # 좌측 벽이 멀면 +yaw(좌회전). 양수 yaw=반시계 가정을 실물에서 확인.
    yaw = max(-.5, min(.5, kp*(left-target)))
    linear = speed * min(1., (front-stop_distance)/stop_distance)
    return linear, yaw, 'TRACK_LEFT_WALL'

def demo():
    return {'straight': wall_command(1., .30), 'blocked': wall_command(.1, .30)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("recon/wall_follower", demo, args)


if __name__ == "__main__":
    main()
