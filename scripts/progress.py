"""Status bookkeeping only; evidence existence does not verify physical success."""
import argparse, json, os
from pathlib import Path
from datetime import datetime, timezone
root=Path(__file__).resolve().parents[1]
path=root/'progress/tasks.json'
p=argparse.ArgumentParser()
sub=p.add_subparsers(dest='cmd',required=True)
sub.add_parser('status')
s=sub.add_parser('set');s.add_argument('id');s.add_argument('status',choices=['TODO','ACTIVE','BLOCKED','REVIEW','VERIFIED'])
s.add_argument('--evidence',action='append',default=[]);s.add_argument('--note',default='')
a=p.parse_args();data=json.loads(path.read_text())
def complete(stage):
    ts=[t for t in data['tasks'] if t['stage']==stage]
    return bool(ts) and all(t['status']=='VERIFIED' for t in ts)
if a.cmd=='status':
    for stage in data['stages']:
        ts=[t for t in data['tasks'] if t['stage']==stage['id']]
        done=sum(t['status']=='VERIFIED' for t in ts)
        waiting=[s for s in stage['depends_on'] if not complete(s)]
        state='VERIFIED' if done==len(ts) else ('WAITING '+','.join(waiting) if waiting else 'READY TO DEVELOP')
        print(f"{stage['id']} {stage['day']:8} {done}/{len(ts)} {state:30} {stage['title']}")
        for t in ts:print(' ',t['id'],t['status'],t['title'])
else:
    task=next((t for t in data['tasks'] if t['id']==a.id),None)
    if task is None:p.error('unknown task id')
    if a.status=='VERIFIED':
        if any(not complete(dep) for dep in task['depends_on']):p.error('prerequisite stage not VERIFIED')
        if not a.evidence:p.error('VERIFIED requires relative evidence paths')
        for name in a.evidence:
            ep=(root/name).resolve()
            if root not in ep.parents or not ep.is_file():p.error('evidence must be an existing file within this project')
    old=task['status'];task.update(status=a.status,evidence=a.evidence,note=a.note)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));os.replace(temp,path)
    with (root/'progress/history.jsonl').open('a') as f:
        f.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),id=a.id,old=old,new=a.status,note=a.note,evidence=a.evidence),ensure_ascii=False)+'\n')
    print(a.id,old,'->',a.status)
