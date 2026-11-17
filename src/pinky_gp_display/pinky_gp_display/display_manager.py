"""D/S08-S10. 최종 적용 상태 -> LED 의미와 LCD 텍스트. 드라이버는 미연결.
2~5Hz timer에서 frame 생성, 이전 frame과 다를 때만 비동기 출력한다.
LCD 오류는 별도 관제 오류이며 이 모듈은 모터 명령을 만들지 않는다.
"""
import math
from pinky_gp_core.display import display_state

def format_time(seconds):
    if seconds is None or not math.isfinite(seconds) or seconds<0: return '--:--.--'
    centiseconds=int(seconds*100)
    minutes,rest=divmod(centiseconds,6000)
    return f'{minutes:02d}:{rest//100:02d}.{rest%100:02d}'

def frame(robot, lap, rank, current, last=None, best=None, total_laps=3, stops=(),
          restriction='NORMAL', drs_active=False, phase='RACING', fresh=False,
          finished=False, penalty_remaining=None):
    led,title=display_state(stops,restriction,drs_active,finished,phase,fresh)
    if not fresh:
        current = last = best = penalty_remaining = None
    timer=f'CURRENT {format_time(current)}'
    primary=timer if title=='LAP TIMER' else title
    if title=='PENALTY': primary=f'PENALTY {format_time(penalty_remaining)}'
    return {'led':led,'primary':primary,'lines':[
        f'{robot} P{rank if rank is not None else "-"} LAP {lap}/{total_laps}',
        timer,f'LAST {format_time(last)}',f'BEST {format_time(best)}'],
        'clock_valid':fresh}

def demo():
    return frame('A',2,1,12.34,28.45,27.81,fresh=True)


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("display/display_manager", demo, args)


if __name__ == "__main__":
    main()
