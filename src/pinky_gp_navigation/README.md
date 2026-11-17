# pinky_gp_navigation 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

