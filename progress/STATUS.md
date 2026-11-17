# 현장 진행 현황

`progress/tasks.json`에서 자동 생성. 코드 가이드 완성과 실물 검증은 별도다.

| 단계 | 일정 | 제목 | VERIFIED | 전체 |
|---|---|---|---:|---:|
| S00 | D1 | 장비와 데이터 계약 | 0 | 4 |
| S01 | D1 | 최종 명령과 정지 | 0 | 4 |
| S02 | D2 | 정찰랩과 SLAM | 0 | 4 |
| S03 | D3 | 지도 확정과 경로 | 0 | 4 |
| S04 | D3 | 단독 경기 주행 | 0 | 4 |
| S05 | D4-D5 | 그리드와 기본 경기 | 0 | 4 |
| S06 | D4-D6 | 랜덤 장애물과 사람 | 0 | 4 |
| S07 | D6 | 깃발과 경기 제한 | 0 | 4 |
| S08 | D7 | SC와 페널티 및 표시 | 0 | 4 |
| S09 | D7-D8 | 추종과 지정 추월 | 0 | 4 |
| S10 | D8 | DRS 연결 | 0 | 4 |
| S11 | D9-D10 | 통합과 배포 | 0 | 4 |
| S12 | 남는 시간 | 아이템과 코너링 보상 | 0 | 4 |

## 작업 목록

| ID | 담당 | 상태 | 작업 |
|---|---|---|---|
| S00-01 | A | TODO | A의 센서 조사 |
| S00-02 | B | TODO | B의 카메라 조사 |
| S00-03 | C | TODO | C의 상태 정의 |
| S00-04 | D | TODO | D의 연결 조사 |
| S01-01 | D | TODO | 제어권 선택 |
| S01-02 | D | TODO | 센서 timeout |
| S01-03 | D | TODO | 중앙 heartbeat timeout |
| S01-04 | D | TODO | 실제 정지 거리 |
| S02-01 | A | TODO | 벽 추종 |
| S02-02 | A | TODO | SLAM 연결 |
| S02-03 | A | TODO | 복귀 판정 |
| S02-04 | A | TODO | 로그 수집 |
| S03-01 | A | TODO | 루프 보정 확인 |
| S03-02 | A | TODO | 중심 경로 추출 |
| S03-03 | A | TODO | 폐곡선과 여유 검사 |
| S03-04 | A | TODO | 지도 B 공유 |
| S04-01 | A | TODO | FollowPath 연결 |
| S04-02 | A | TODO | RPP 비교 |
| S04-03 | A | TODO | 필요 시 MPPI 비교 |
| S04-04 | A | TODO | 곡률 속도 상한 |
| S05-01 | D | TODO | 칸별 표식 |
| S05-02 | D | TODO | 순차 정렬 |
| S05-03 | D | TODO | 출발등 |
| S05-04 | D | TODO | 랩 및 체커 |
| S06-01 | B | TODO | YOLO 데이터 |
| S06-02 | B | TODO | 거리 연관 |
| S06-03 | B | TODO | 콘과 볼라드 회피 |
| S06-04 | B | TODO | 사람 정지와 해제 |
| S07-01 | C | TODO | 옐로 |
| S07-02 | C | TODO | 그린 시각 조건 |
| S07-03 | C | TODO | 레드 terminal |
| S07-04 | C | TODO | 명령 중복 배제 |
| S08-01 | C/D | TODO | SC 순서 유지 |
| S08-02 | C/D | TODO | 실제 정지 페널티 계시 |
| S08-03 | C/D | TODO | LED LCD |
| S08-04 | C/D | TODO | 랩시간 표시 |
| S09-01 | A/C | TODO | 앞차 식별 |
| S09-02 | A/C | TODO | 후보 경로 검사 |
| S09-03 | A/C | TODO | PASS MERGE |
| S09-04 | A/C | TODO | 추월 취소 |
| S10-01 | C | TODO | 검출선 자격 |
| S10-02 | C | TODO | 사용 구간 |
| S10-03 | C | TODO | 최종 속도 제한 |
| S10-04 | C | TODO | 초록 LED |
| S11-01 | ALL | TODO | 랜덤 시험 |
| S11-02 | ALL | TODO | 통신 fault |
| S11-03 | ALL | TODO | 실행 설명 |
| S11-04 | ALL | TODO | 모델 설정 동결 |
| S12-01 | C | TODO | 획득 ID |
| S12-02 | C | TODO | 부스터 |
| S12-03 | C | TODO | 감속 |
| S12-04 | C | TODO | 코너 보상 |
