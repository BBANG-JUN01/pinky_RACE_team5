# 모듈별 구현 가이드

모든 예제는 ROS 없이 동작한다. 입력은 문서에 적힌 단위/좌표계/시계를 지킨다. 실제 입력 검증과 ROS 메시지 변환을 추가하기 전에는 모터에 연결하지 않는다.

공통 작업 순서: `--demo` 출력 확인 → 관련 테스트 읽기 → 기록 데이터 입력 → ROS adapter 작성 → 로봇 정지 시험 → 저속 실측.

## guard.command_guard

D/S01. 제어권·신선도·정지 사유를 통과한 후보만 반환하는 순수 로직.
출력은 (linear m/s, angular rad/s, reason). 실제 base 토픽 발행은 미연결.
하드웨어 adapter에서 이 함수 결과만 발행하고 base 자체 watchdog도 검증한다.

핵심 API: `Velocity, CommandGuard`

```bash
python3 scripts/run_module.py guard.command_guard --demo
```

## guard.robot_health

D/S00-S01. 각 입력의 수신 시각을 같은 로컬 monotonic clock으로 관리.
ROS 연결: scan/odom/vision/중앙 heartbeat callback에서 touch(), timer에서 faults().
촬영 stamp의 시간 동기화/역행/중복 검사는 callback의 별도 책임이다.

핵심 API: `HealthMonitor`

```bash
python3 scripts/run_module.py guard.robot_health --demo
```

## recon.map_finalize

A/S03. 지도+검증된 경로 파일의 버전 manifest 작성 가이드.
SLAM loop closure 이후 경로 재구성과 footprint 충돌 검사는 미구현이다.
이 함수는 외부 검사 완료 여부를 입력받으며 검사 성공을 스스로 증명하지 않는다.

핵심 API: `manifest`

```bash
python3 scripts/run_module.py recon.map_finalize --demo
```

## recon.recon_manager

A/S02. 시작 구역 이탈·최소 이동·진행 방향·표식 재관측으로 복귀 판정.
SLAM 시작/저장 서비스는 외부 adapter에서 호출. RETURNED는 MAP_READY가 아니다.

핵심 API: `ReconManager`

```bash
python3 scripts/run_module.py recon.recon_manager --demo
```

## recon.wall_follower

A/S02. 왼쪽 벽 추종 P 제어 기준 예제. 실제 조향 튜닝 전 저속 bag 재생용.
입력은 base frame 기준 전방/좌측 유효 거리. LaserScan 각도 영역 추출은 adapter 책임.
후속: 양쪽 벽 선택, PID 적분 anti-windup, 코너 탈출, scan timestamp 검증.

핵심 API: `sector_distance, wall_command`

```bash
python3 scripts/run_module.py recon.wall_follower --demo
```

## navigation.grid_manager

A/S05. 순차 접근 후 마커 상대 오차 기반 저속 정렬 예제.
목표를 로봇 base frame으로 변환한 x/y(m), yaw(rad)를 전달한다.
상대 로봇 점유·표식 유실 시 정지. READY는 정지 관측과 연속 허용오차가 필요하다.

핵심 API: `GridAligner`

```bash
python3 scripts/run_module.py navigation.grid_manager --demo
```

## navigation.nav2_adapter

A/S04. 비동기 FollowPath 연결을 위한 transport-independent 계약.
실제 Nav2 action 호출은 미연결. 아래 transport protocol을 구현하고 ROS executor에서
feedback/result/cancel callback을 이 상태 기계에 전달한다. 취소 ACK 전 새 goal 금지.

핵심 API: `NavigationSession`

```bash
python3 scripts/run_module.py navigation.nav2_adapter --demo
```

## navigation.path_manager

A/S03. 폐곡선 경로 길이·근방 투영 가이드.
완성된 중심선 추출기가 아니다. 입력 마지막 점은 첫 점을 반복하지 않는다.
벽/로봇 외곽 여유, 전체 선분 충돌 검사는 지도 adapter에서 별도 수행한다.

핵심 API: `LoopPath`

```bash
python3 scripts/run_module.py navigation.path_manager --demo
```

## perception.detector

B/S06. YOLO 등 외부 모델 출력 정규화 가이드. 모델 로딩/추론은 미연결.
rows=[{label, confidence, xyxy:[x1,y1,x2,y2]}], 픽셀 단위.
빈 결과는 '사람 없음'의 충분조건이 아니다. frame freshness와 추론 상태를 함께 전달.

핵심 API: `normalize`

```bash
python3 scripts/run_module.py perception.detector --demo
```

## perception.grid_reader

B/S05. 외부 ArUco/표식 pose 추정 결과에서 배정된 칸 하나만 선택.
코너 검출, 카메라 intrinsic/extrinsic, pose 좌표 변환은 adapter에서 구현.

핵심 API: `select_target`

```bash
python3 scripts/run_module.py perception.grid_reader --demo
```

## perception.range_association

B/S06. 보정 완료한 카메라 ROI에 투영된 LiDAR 후보 거리의 보수적 연관 예제.
입력은 양 센서 시간 동기화 후 ROI에 투영한 거리들이다. TF/투영 자체는 미구현.
서로 다른 깊이 군집이 섞이면 invalid. 단안 박스 크기로 거리를 추측하지 않는다.

핵심 API: `associate`

```bash
python3 scripts/run_module.py perception.range_association --demo
```

## perception.signal_reader

B/S05-S07. 출발등 1..N 순차 점등 후 안정된 0 관측만 승인.
ROI 유실/영상 stale/순서 오류는 시퀀스를 취소. 깃발 RED/GREEN은 별도 RacePolicy 사용.
동일 프레임 중복을 거부하고 다음 경기에는 새 인스턴스를 사용한다.

핵심 API: `StartLights`

```bash
python3 scripts/run_module.py perception.signal_reader --demo
```

## race.penalty_manager

C/S08. 로봇별 연속 정지 계시와 중복 ID 배제.
실제 odom 선속도/각속도가 모두 허용치 이하이고 fresh일 때만 stopped=True로 입력.
해제 출력은 PENALTY 사유에만 적용하며 PERSON/RED/ESTOP는 유지한다.

핵심 API: `PenaltyManager`

```bash
python3 scripts/run_module.py race.penalty_manager --demo
```

## race.progress_manager

C/S05. 검증된 checkpoint 이벤트를 LapTimer에 전달하고 순위 계산.
pose -> gate 교차, 방향, teleport 거부는 외부 측정 adapter 책임. 수신 시각으로 재계시 금지.

핵심 API: `ProgressManager, ranking`

```bash
python3 scripts/run_module.py race.progress_manager --demo
```

## race.race_manager

C/S05-S07. 명시적 조건을 확인하는 생애 FSM, RED terminal.
조건 evidence는 adapter가 실제 관측으로 생성해야 한다. 운영자 버튼만으로 True 금지.
새 경기 RESET은 새 인스턴스/새 race_id로 수행하며 ESTOP 해제와 분리한다.

핵심 API: `RaceManager`

```bash
python3 scripts/run_module.py race.race_manager --demo
```

## behavior.behavior_manager

C/S09. 추월 FSM 가이드. 공간 검사는 호출자가 전체 후보/합류 경로에 수행.
ABORT는 원래 경로 강제 복귀가 아니다. 정지 후 안전 재계획과 새 시도 필요.
SC 순서 고정/앞차 추종은 별도 progress+speed 정책에서 처리한다.

핵심 API: `OvertakeManager`

```bash
python3 scripts/run_module.py behavior.behavior_manager --demo
```

## behavior.speed_policy

C/S07-S10. 제한 속도와 곡률/앞차 상한 결합. DRS는 실제 상한 증가 때만 active.
수치는 합성 예제용. 제동 거리/통신 지연 측정 후 교체한다.

핵심 API: `speed_limit`

```bash
python3 scripts/run_module.py behavior.speed_policy --demo
```

## display.display_manager

D/S08-S10. 최종 적용 상태 -> LED 의미와 LCD 텍스트. 드라이버는 미연결.
2~5Hz timer에서 frame 생성, 이전 frame과 다를 때만 비동기 출력한다.
LCD 오류는 별도 관제 오류이며 이 모듈은 모터 명령을 만들지 않는다.

핵심 API: `format_time, frame`

```bash
python3 scripts/run_module.py display.display_manager --demo
```

## dashboard.operator_server

D/S05-S08. 관제 명령 생성 계약. HTTP 서버/인증/ROS 서비스는 미연결.
운영 UI는 여기서 생성한 command_id를 재전송에도 유지한다.
accepted와 실제 완료를 구분해서 표시하고 모든 요청/결과를 JSONL로 기록한다.

핵심 API: `OperatorCommand`

```bash
python3 scripts/run_module.py dashboard.operator_server --demo
```

## 선택 확장 S12

필수 기능 통과 후 `behavior/effects_manager.py`를 추가한다. 획득 ID를 race_id와 묶어 중복 소모를 거부하고, 효과 만료는 중앙 단조 증가 시계로 계산한다. 부스터는 하드웨어/앞차/코너 상한을 넘지 않고, 상대 감속은 대상 로봇 ID를 명시한다. 코너 에너지는 유효 구간 진입·이탈과 쿨다운을 검증한다. 아이템/코너 보상은 현재 코드가 없으며 기본 설정은 비활성이다.
