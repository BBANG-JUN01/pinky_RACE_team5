# Git과 노션으로 개발 진행 관리

## 역할

| 역할 | 주 담당 | 매일 남길 결과 |
|---|---|---|
| A | 정찰·지도·경로·Nav2·그리드 | 지도/경로 버전, 경로 오차와 완주 로그 |
| B | 비전·출발등·깃발·거리 연관 | 촬영 세션, 오검출/미검출, 지연 |
| C | 경기 규칙·랩·페널티·추월·DRS | 상태 전이 테스트, 명령과 결과 |
| D | 통합·guard·통신·표시·관제 | 토픽/TF 계약, 끊김 시험, 장치 출력 |

이름은 첫 회의에서 매핑한다. S00의 A/B/C 조사 작업도 해당 역할 담당으로 수정했다.

## 한 작업의 흐름

1. `progress/tasks.json`에서 선행 단계와 완료 조건을 확인한다.
2. 작업 ID로 브랜치를 만든다. 예: `feat/S01-02-sensor-timeout`.
3. `python3 scripts/progress.py set S01-02 ACTIVE --note '구현 시작'`로 상태를 기록한다.
4. 코드·설정·테스트와 증거 문서를 같은 브랜치에 커밋한다.
5. PR에 문제, 구현, 실행 명령, 결과, 남은 현장 검증을 적는다.
6. 검토 후 병합한다. 증거가 확보된 작업만 VERIFIED로 올린다.

```bash
git switch -c feat/S00-01-sensor-inventory
python3 scripts/progress.py set S00-01 ACTIVE --note 'A 실제 토픽 조사'
python3 scripts/check_core.py
```

증거 파일을 실제로 작성한 뒤:

```bash
python3 scripts/progress.py set S00-01 VERIFIED --evidence evidence/S00-01.md --note '두 로봇의 scan/odom 형식 확인'
python3 scripts/export_progress.py
```

VERIFIED는 파일 존재 검사뿐 아니라 담당자/리뷰어가 실측 내용을 검토해야 한다.
의존 단계가 미완료면 진행 도구가 VERIFIED를 거부한다. BLOCKED에는 원인과 필요한 입력을 적는다.

## 노션 구성

프로젝트 홈 아래 `작업 보드`, `실험 기록`, `결정 기록`, `장비/실행 안내`를 둔다.
Git을 코드·테스트·작업 상태의 기준으로 사용하고 노션에는 맥락·사진·회의·결정 근거를 남긴다.

| 작업 DB 속성 | 값 |
|---|---|
| 이름 | 작업 제목 |
| 작업 ID | S00-01 등 |
| 단계 | S00~S12 |
| 상태 | TODO / ACTIVE / BLOCKED / REVIEW / VERIFIED |
| 담당 | A~D → 실제 팀원 |
| 선행 단계 | depends_on |
| Git 링크 | 관련 PR/commit |
| 검증 증거 | evidence 문서/실험 페이지 |

`python3 scripts/export_progress.py`는 `progress/NOTION_TASKS.csv`와 `progress/STATUS.md`를 생성한다.
CSV는 노션 최초 가져오기용이며 반복 가져오기는 중복 행을 만들 수 있다.
이 저장소에 노션 자동 동기화나 노션 API 키는 포함하지 않았다. 기존 DB 업데이트는 작업 ID 기준으로 수행한다.

매일 시작: status와 BLOCKED 확인 → 오늘 최대 1~2개 작업 선택.
매일 종료: 테스트 결과·실패 원인 기록 → 상태/CSV 갱신 → 다음 담당자에게 입력 계약 공유.
D5 통합, D8 기능 동결, D9~D10 회귀 검증 원칙을 유지한다.
