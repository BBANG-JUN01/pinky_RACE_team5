# 가이드 코드를 실제 ROS 노드에 연결하는 순서

## 1. 실제 장비 계약 확정 (D)

`hardware_inventory.example.yaml`을 복사하고 A/B 각각 실제 scan/odom/image/camera_info/TF/명령 토픽과 메시지 형식을 기록한다.
제조사 드라이버·ROS 배포판·git commit·센서 시각을 적는다. `Twist`인지 `TwistStamped`인지 확인 후 타입을 고정한다.
두 로봇의 프레임과 토픽이 섞이지 않게 하고, 중앙과 로봇의 monotonic 시각을 직접 비교하지 않는다.

읽기 전용 조사 예:

```bash
ros2 topic list -t
ros2 node list
ros2 topic info <실제_scan_토픽> --verbose
ros2 interface show <실제_명령_메시지_타입>
```

## 2. 순수 함수와 ROS adapter 분리 (전체)

현재 각 `main()`은 데모 CLI다. 실제 노드를 추가할 때 알고리즘 클래스를 유지하고 별도 `*_node.py`를 만든다.
`setup.py`에 별도 console entry를 추가하고 `package.xml`에 사용하는 ROS 의존성만 추가한다.
ROS 노드 형태는 다음 순서를 따른다.

```python
# 구조 의사코드: 이 블록 자체는 실행 파일이 아니다.
class RobotNode:
    def on_sensor(self, msg):
        # 원래 stamp/프레임/값을 검증하고 최신 입력만 교체한다.
        # HealthMonitor.touch에는 동일 프로세스 monotonic 수신 시각을 사용한다.
        pass

    def on_control_timer(self):
        # freshness 확인 → 알고리즘 호출 → 후보 명령/상태 발행
        # blocking 추론, 파일 저장, 동기 service 대기는 여기서 하지 않는다.
        pass
```

| 연결 순서 | 입력 → 코드 → 출력 | 실패 시 |
|---|---|---|
| 1 | 센서/heartbeat → HealthMonitor → faults | 입력 없으면 준비 불가 |
| 2 | 후보 명령 + phase + stop → CommandGuard → 최종 base 명령 | zero command, base watchdog 확인 |
| 3 | LaserScan 영역 거리 → wall_command → recon 후보 | 유효 거리 없으면 정지 |
| 4 | 정찰 상태 → ReconManager → SLAM 종료/저장 요청 | timeout FAILED |
| 5 | 최종 지도 → 경로 추출·충돌 검사 → manifest/LoopPath | 승인 보류 |
| 6 | path + localization → 실제 Nav2 action → nav 후보 | 취소 ACK/실패 처리 |
| 7 | 카메라 모델 → normalize/associate/select_target | invalid를 탐지 없음과 분리 |
| 8 | grid 관측 → GridAligner → grid 후보/READY | 유실 시 READY 해제 |
| 9 | 명령·영상 출발등 → RaceManager/StartLights | 승인 조건 없으면 START 거부 |
| 10 | gate 교차 → ProgressManager + PenaltyManager | 점프/역주행/오래된 odom 거부 |
| 11 | 상대 위치·경로 → OvertakeManager/speed_limit | 금지/충돌 시 취소·정지 |
| 12 | 최종 적용 상태 → display.frame → 실제 LED/LCD | 오래된 DRS 표시 해제 |

## 3. 중앙 경기 상태 묶기 (C)

RaceManager는 생애 상태, RacePolicy는 제한, StopReasons는 로봇별 정지 사유를 담당한다.
SC_ON/YELLOW/GREEN/RED는 같은 처리 주기에서 모아 `signals(events)`로 전달한다. RED가 우선한다.
`race_id`, 명령 권한, 촬영 시각·신선도를 먼저 확인한다. 단독 `command(RED)`도 ABORTED를 만든다.

중앙 START 승인 시각 하나로 두 로봇 LapTimer를 시작한다. 출발등 ROI 유효성과 두 대 GRID_READY를 다시 확인한다.
RED를 받으면 ProgressManager.abort로 시간을 고정하고 로봇별 RED 정지 사유를 설정한다.
CHECKER 승인 후 progress.checker를 True로 바꾸고 각 로봇의 다음 유효 결승선에서 기록을 고정한다.
모든 로봇 완주와 실제 정지 후 FINISH한다. 정지 중에도 timer는 계속 흐른다.

페널티의 measured_stopped는 신선한 odom의 선속도/각속도 모두로 판단한다.
페널티 완료 시 `StopReasons.set('PENALTY', False)`만 호출한다. 전체 reasons를 비우지 않는다.

## 4. 반드시 추가할 부분

- gate 판정: 이전/현재 pose의 결승선 교차, 올바른 방향, 구간 순서, 최대 변위·속도 검사.
- 경로 생성: loop closure 후 보정된 지도, 폐곡선 연결, footprint+여유에 대한 전체 선분 충돌 검사.
- Nav2: 서버 생애/goal accept/feedback/result/cancel/timeouts, 저속 순환 경로 분할, controller 출력 remap.
- perception: 모델 버전/클래스, 카메라 캘리브레이션, 시간 동기화, TF를 적용한 LiDAR 투영.
- guard: 후보 출처별 저장소, phase 기반 선택, 센서와 중앙 끊김, 로봇 base watchdog.
- display: snapshot의 revision/수신 나이, 무효 기록은 `--:--.--`, 실제 DRS 활성과 장치 오류.
- dashboard: 명령 ACK와 완료 분리, 접근 제어, append-only 이벤트 로그, UI의 거절 이유 표시.

SC 순서 고정과 사람 정지 해제의 안정 관측 시간은 아직 별도 구현해야 한다.
예제 `fresh=True`, `clear=True`를 실물 코드에 상수로 복사하지 않는다.

## 5. 실행 통합과 완료

`hardware.launch.py`의 차단은 미연결 상태를 표현한다. 이를 단순 삭제해 실행하지 말고
드라이버/센서/guard/알고리즘 노드·namespace·remap을 완성한 launch로 교체한다.
`race_defaults.yaml`의 null 값은 실측값으로 채우고 설정 파일 loader와 검증을 작성한다.
현재 Python 함수 기본값은 YAML에서 자동 로드되지 않는 합성 예제값이다.

각 adapter는 bag 재생 → 바퀴 분리/고정 시험 → 저속 트랙 시험 순으로 검증한다.
ROS 빌드, 드라이버 버전, 전체 시험 횟수와 실패를 기록한 뒤 해당 현장 작업을 VERIFIED로 바꾼다.
