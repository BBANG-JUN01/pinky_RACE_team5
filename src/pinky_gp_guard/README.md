# pinky_gp_guard 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

