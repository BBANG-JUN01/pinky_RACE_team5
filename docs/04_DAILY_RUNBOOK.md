# 일일 실행과 진행 확인

## 첫 2시간

1. 담당 A/B/C/D와 저장소, D1 날짜를 확정한다.
2. 두 로봇의 OS·SBC·패키지 commit·센서 토픽·TF·속도 명령 타입을 조사한다.
3. 실제 최종 모터 토픽에 누가 publish하는지 확인한다. 기존 teleop/Nav2와 중복 금지.
4. 현재 폴더를 별도 workspace로 복사하고 core 테스트와 status를 실행한다.
5. 토픽 목록, 프레임 트리, 정지 시험 결과를 evidence/S00에 남긴다.
6. cmd_vel 경로와 timeout 정지가 확인되기 전 자동 정찰을 실행하지 않는다.

## 매일 시작 15분

- progress.py status에서 선행 단계, BLOCKED, REVIEW를 확인한다.
- 오늘의 통과 기준 하나와 공동 통합 시간을 정한다.
- 어제 사용한 map/path/model/config 버전과 배터리·네트워크를 확인한다.

## 낮 통합

한 번에 한 계층만 연결한다. 먼저 저장된 입력으로 출력 형식을 확인하고,
저속 단독 시험 → 두 대 시험 순서로 진행한다. 가짜 입력은 demo 모드에서만 사용한다.
하드웨어 로그에는 synthetic 여부를 명시하고 성공률에 가짜 재생을 섞지 않는다.

## 종료 전 30분

1. 변경 코드와 설정을 commit한다. 실제 repository URL은 팀이 생성한 뒤 기록한다.
2. 재현 명령, 시도 수·성공 수, 영상/bag 위치와 실패를 result.md에 기록한다.
3. 작업을 REVIEW로 전환하고 다른 담당이 확인한 후 VERIFIED로 변경한다.
4. 다음 작업자가 사용할 입력과 담당자를 기록한다.
5. 당일 정상 실행 방법과 멈추는 방법을 README에 반영한다.

## 진행 명령 예시

```bash
python3 scripts/progress.py status
python3 scripts/progress.py set S00-01 ACTIVE --note 'A 센서 토픽 조사 시작'
python3 scripts/progress.py set S00-01 REVIEW --note '증거 검토 요청'
python3 scripts/progress.py set S00-01 VERIFIED --evidence evidence/S00/result.md --note '담당 외 검토자와 검증 환경 기록'
python3 scripts/progress.py set S03-02 BLOCKED --note '루프 폐쇄 후 경로 불연속; A가 보정 필요'
```

위 명령은 예시다. 검증 결과 없이 일괄 VERIFIED로 변경하지 않는다.
진행 파일 갱신은 한 사람이 순차 수행한다. 다중 쓰기 잠금은 구현하지 않았다.

## 일정이 밀릴 때

D3에 정찰 지도에서 주행이 안 되면 제어기 후보를 더 늘리지 않는다.
D5에 기본 경기를 못 끝내면 추월·DRS보다 정찰→그리드→완주 통합을 먼저 고친다.
D8 이후 아이템·코너링 기능은 시작하지 않는다. 축소한 필수 기능은 미완료로 남기고
시연 제약과 이유를 공개한다. 기획 요구를 조용히 삭제하지 않는다.
