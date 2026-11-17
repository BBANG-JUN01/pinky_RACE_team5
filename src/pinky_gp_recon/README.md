# pinky_gp_recon 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

