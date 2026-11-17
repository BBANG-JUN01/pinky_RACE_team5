# pinky_gp_perception 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

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

