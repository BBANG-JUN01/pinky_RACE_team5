"""가이드 클래스 연결 예: 준비→출발→SC→페널티→체커. 합성 입력만 사용."""
from pathlib import Path
import sys,json
root=Path(__file__).resolve().parents[1]
for p in (root/'src').glob('pinky_gp_*'):sys.path.insert(0,str(p))
from pinky_gp_race.race_manager import RaceManager
from pinky_gp_race.progress_manager import ProgressManager
from pinky_gp_race.penalty_manager import PenaltyManager
from pinky_gp_core.policy import StopReasons
from pinky_gp_behavior.speed_policy import speed_limit
from pinky_gp_display.display_manager import frame

race=RaceManager('synthetic-demo')
progress=ProgressManager(); penalties=PenaltyManager();stops=StopReasons()
evidence=dict.fromkeys(['healthy','guard_ready','map_valid','path_valid','shared','localized','both_ready','lights_valid'],True)
# These booleans describe a synthetic fixture, never real sensor readiness.
for i,kind in enumerate(['CHECK','RECON','MAP_READY','GRID','ARM_START','START']):
    assert race.command('synthetic-demo',str(i),kind,evidence)
progress.start(0.)
def emit(now, remaining=None):
    s=progress.snapshot('A',now)
    cap,drs=speed_limit(race.policy,stops,0.,2.,True,True,True)
    screen=frame('A',s['completed_laps'] if s['finished'] else s['completed_laps']+1,None,s['current'],s['last'],s['best'],
                 stops=stops.reasons,restriction=race.policy.restriction.value,
                 drs_active=drs,phase=race.phase,fresh=True,finished=s['finished'],total_laps=1,penalty_remaining=remaining)
    print(json.dumps({'mode':'SYNTHETIC_ONLY','at':now,'phase':race.phase,
                      'speed_cap':cap,'display':screen},ensure_ascii=False))
emit(1.)
race.signals([('synthetic-demo','sc','SC_ON',2.)]);emit(2.)
penalties.issue('penalty-1','A',2.)
for now in (3.,4.,5.):
    state=penalties.update('A',now,True,True)
    stops.set('PENALTY',state['stop']);emit(now,state['remaining'])
race.signals([('synthetic-demo','green','GREEN',6.)]);emit(6.)
race.command('synthetic-demo','checker','CHECKER');progress.checker=True
for robot in ('A','B'):
    for name,at in [('CP1',7.),('CP2',8.),('FINISH',9.)]:progress.gate(robot,name,at)
race.command('synthetic-demo','finished','FINISH',{'all_finished':True,'all_stopped':True})
stops.set('FINISHED',True)
emit(10.)
