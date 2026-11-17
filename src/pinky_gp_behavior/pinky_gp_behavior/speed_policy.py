"""C/S07-S10. 제한 속도와 곡률/앞차 상한 결합. DRS는 실제 상한 증가 때만 active.
수치는 합성 예제용. 제동 거리/통신 지연 측정 후 교체한다.
"""
import math
from pinky_gp_core.policy import effective_speed

def speed_limit(race, stops, curvature, front_gap, fresh, drs_requested=False, zone=False,
                base=.12, hardware=.20, drs_cap=.18, yellow=.07, sc=.06,
                lateral_accel=.08, stop_gap=.30, time_headway=1.5):
    vals=(curvature,front_gap,base,hardware,drs_cap,yellow,sc,lateral_accel,stop_gap,time_headway)
    if not all(math.isfinite(x) for x in vals) or min(vals[1:])<0 or time_headway<=0 or lateral_accel<=0:
        return 0.,False
    curve_cap=math.sqrt(lateral_accel/max(abs(curvature),1e-6))
    follow_cap=max(0.,(front_gap-stop_gap)/time_headway)
    restriction_cap={'NORMAL':hardware,'YELLOW':yellow,'SC':sc}[race.restriction.value]
    return effective_speed(base,hardware,min(curve_cap,follow_cap,restriction_cap),race,stops,
                           drs_requested,drs_cap,zone,fresh,front_gap>stop_gap)

def demo():
    from pinky_gp_core.policy import RacePolicy,StopReasons
    return {'drs':speed_limit(RacePolicy('demo'),StopReasons(),0.,2.,True,True,True),
            'front_blocked':speed_limit(RacePolicy('demo'),StopReasons(),0.,.2,True,True,True)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("behavior/speed_policy", demo, args)


if __name__ == "__main__":
    main()
