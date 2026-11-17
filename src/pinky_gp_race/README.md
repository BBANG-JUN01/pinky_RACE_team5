# pinky_gp_race 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

