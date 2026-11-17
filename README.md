# Pinky GP · pinky_RACE_team5

Pinky Pro 두 대가 **정찰 → 지도·경로 확정 → 자동 그리드 정렬 → 출발등 → 경기 → 완주/레드 종료**를 수행하는 ROS 2 Jazzy 프로젝트.
기준: 기획서 v1.2, 4명, 실작업 10일. 전면 LCD 랩타임과 후면 LED 상태 표시를 포함한다.

> 현재 배포는 **개발 가이드 v0.2**다. 19개 기능 모듈에 오프라인 실행 예제와 기본 판단 로직을 제공한다.
> 실제 센서·YOLO·SLAM·Nav2·모터·LED/LCD 연결은 아직 구현되지 않았다. ROS 노드 네트워크나 완성된 자율주행 프로그램으로 사용하지 않는다.

## 바로 확인하기

Python 3.10 이상, 추가 패키지 없이 저장소 루트에서 실행한다.

```bash
python3 scripts/check_core.py
python3 scripts/replay_demo.py
python3 scripts/race_scenario.py
python3 scripts/run_module.py race.race_manager --demo
python3 scripts/run_module.py display.display_manager --demo
python3 scripts/guide_smoke.py
python3 scripts/progress.py status
```

45개 자동 테스트가 경기 규칙·정지·timeout·랩 계시·출발등·추월 취소 등을 검사한다.
모듈 예제는 합성 데이터이며 실제 주행 명령을 보내지 않는다.
`python3 scripts/run_module.py <영역>.<모듈> --demo`로 각 예제를 실행한다.

## 읽는 순서

| 순서 | 문서 | 용도 |
|---|---|---|
| 1 | [현재 구현 상태](docs/IMPLEMENTATION_MATRIX.md) | 구현/가이드/미연결 구분 |
| 2 | [개발 시작 안내](docs/01_DEVELOPMENT_GUIDE.md) | 역할과 우선순위 |
| 3 | [모듈별 코드 가이드](docs/07_MODULE_GUIDE.md) | 각 파일 입력·출력·후속 구현 |
| 4 | [ROS 연결 절차](docs/08_ROS_ADAPTER_GUIDE.md) | 예제 함수를 실제 노드로 연결 |
| 5 | [단계별 통과 기준](docs/03_STAGES.md) | S00~S12 검증 |
| 6 | [Git·노션 운영](docs/09_TEAM_WORKFLOW.md) | 브랜치·작업·증거 관리 |
| 참고 | [전체 기획](docs/PROJECT_PLAN.md) · [인터페이스](docs/02_INTERFACES.md) · [파일 목록](docs/CODE_TREE.md) | 요구사항과 구조 |

## 패키지와 분담

| 패키지 | 담당 역할 | 현재 제공 |
|---|---|---|
| pinky_gp_core | 공통 | 제한·정지·DRS·랩 계시·표시 우선순위 |
| pinky_gp_interfaces | 공통 | 9개 메시지, 1개 서비스 초안 |
| pinky_gp_guard | D | 입력 timeout·제어권·명령 제한 가이드 |
| pinky_gp_recon | A | 벽 추종 P 제어·복귀 판정·지도 manifest |
| pinky_gp_navigation | A | 경로 투영·그리드 정렬·Nav2 goal 생애 계약 |
| pinky_gp_perception | B | 검출 정규화·거리 연관·출발등·마커 선택 |
| pinky_gp_race | C | 경기 생애·랩/순위·페널티 |
| pinky_gp_behavior | C | 추월 FSM·제한 속도/DRS 정책 |
| pinky_gp_display | D | LED 의미·LCD 현재/직전/베스트 랩 화면 |
| pinky_gp_dashboard | D | 관제 명령 검증·ID 생성 |
| pinky_gp_bringup | D | 설정 초안·실물 launch 연결 전 차단 |

A~D는 역할 코드이며 팀원 이름을 추측해 배정하지 않았다.

## 개발 순서

1. **D1 / S00~S01**: 실제 토픽·TF·장비 버전 조사 → 로봇별 최종 명령 소유권·정지 검증.
2. **D2~D3 / S02~S04**: 정찰·SLAM → 루프 보정 경로·지도 공유 → 단독 완주.
3. **D4~D5 / S05~S06**: 그리드·출발등·두 대 기본 경기 → 사람·장애물 대응.
4. **D6~D8 / S07~S10**: 깃발·SC·페널티·LED/LCD → 지정 추월·DRS.
5. **D9~D10 / S11**: 기능 동결·반복 시험·로그와 시연. S12 아이템/코너 보상은 선택.

현장 작업 52개는 `progress/tasks.json`에서 TODO로 시작한다. 가이드 코드 추가를 현장 완료로 집계하지 않는다.

```bash
python3 scripts/progress.py set S00-01 ACTIVE --note 'A 센서 토픽 조사 시작'
python3 scripts/progress.py status
python3 scripts/export_progress.py
```

## ROS 환경에서 빌드할 때

이 저장소 자체가 workspace 형태이며 `src/`에 프로젝트 패키지가 있다.
기존 `~/pinky_gp_ws/src` 아래 clone했다면 해당 workspace 루트에서 colcon을 실행한다.
제조사 저장소는 별도로 유지하고 설치 버전을 기록한다.

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
ros2 run pinky_gp_race race_manager --demo
```

위 `ros2 run`도 오프라인 CLI를 실행한다. ROS 구독·발행을 시작하지 않는다.
**colcon/rosidl 빌드와 하드웨어 실행은 이 배포에서 미검증**이다.
하드웨어 launch는 구현 전 차단 상태이며 설정의 `hardware_enabled`만 바꿔도 주행하지 않는다.

## 경기 규칙 핵심

- RED는 해당 경기 종료. GREEN으로 재출발하지 않는다.
- GREEN은 YELLOW/SC 제한만 해제하고 PERSON/PENALTY/ESTOP 정지 사유를 지우지 않는다.
- 페널티는 실제 정지 확인 후 계시. 랩 시간은 옐로/SC/사람 정지/페널티 중에도 흐른다.
- 유효 체크포인트 순서와 방향이 충족된 결승선 통과만 랩으로 인정한다.
- DRS 자격과 실제 활성은 구분한다. 후면 초록 LED는 실제 추가 출력 허용 시에만 표시한다.
- 실물 기본 속도와 timeout은 미측정이며, 코드 예제 수치는 합성 시험용이다.

[검증 결과](docs/VALIDATION.md) · [변경 이력](CHANGELOG.md) · [개발 규칙](CONTRIBUTING.md)
