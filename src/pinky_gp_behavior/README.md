# pinky_gp_behavior 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

