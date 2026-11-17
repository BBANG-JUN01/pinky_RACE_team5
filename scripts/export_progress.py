"""Git 작업 상태를 Markdown과 노션 최초 가져오기용 CSV로 내보낸다."""
from pathlib import Path
import csv,json
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'progress/tasks.json').read_text())
tasks=data['tasks'];stages={s['id']:s for s in data['stages']}
with (root/'progress/NOTION_TASKS.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(['이름','작업 ID','단계','상태','담당','일정','선행 단계','검증 증거','메모'])
    for t in tasks:
        writer.writerow([t['title'],t['id'],t['stage'],t['status'],t['owner'],stages[t['stage']]['day'],
                         ', '.join(t['depends_on']),', '.join(t['evidence']),t['note']])
lines=['# 현장 진행 현황','','`progress/tasks.json`에서 자동 생성. 코드 가이드 완성과 실물 검증은 별도다.','',
       '| 단계 | 일정 | 제목 | VERIFIED | 전체 |','|---|---|---|---:|---:|']
for s in data['stages']:
    group=[t for t in tasks if t['stage']==s['id']]
    lines.append(f"| {s['id']} | {s['day']} | {s['title']} | {sum(t['status']=='VERIFIED' for t in group)} | {len(group)} |")
lines+=['','## 작업 목록','','| ID | 담당 | 상태 | 작업 |','|---|---|---|---|']
for t in tasks:lines.append(f"| {t['id']} | {t['owner']} | {t['status']} | {t['title']} |")
(root/'progress/STATUS.md').write_text('\n'.join(lines)+'\n')
print(f'Exported {len(tasks)} tasks to progress/STATUS.md and progress/NOTION_TASKS.csv')
