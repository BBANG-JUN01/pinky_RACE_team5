# 11월 21일 토요일 준비 현황

일정 근거: 11/20까지 시뮬레이션 1대 3랩, 11/21 실물 데이터 수집과 1대 완주. 2대 경쟁·플래그·DRS·추월은 후속 일정이다.

## 구현과 검증
- 폐곡선 Pure Pursuit: 위치 투영, 전방 목표, 곡률 기반 차동구동 속도, 각속도 제한, 경로 이탈/비정상 위치 차단.
- 주행 거리 누적 랩 판정: 위치 도약 차단, 역주행/결승선 떨림 오계수 방지. 공식 경기 체크포인트 판정과는 별도 시험용이다. 시작 위치를 기준으로 1바퀴를 센다.
- ROS tracking_node: 경로와 동일 frame의 PoseStamped 입력, 촬영 시각/수신 timeout, enable, 3랩 완료 후 0 후보 명령. candidate/nav만 발행한다. 최종 모터 guard는 별도 연결해야 한다.
- S00 수집기 및 상태형 S01 guard_core도 통합했다. 기존 가이드 API는 보존한다.
- 기본/가이드/추종 테스트 54개, 별도 guard 12개 통과. 기존 19개 모듈 smoke 실행 통과.
- 10개 seed의 타원 경로에서 각 3랩 완주. 입력 초기 오차와 구동 오차를 준 운동학 시험이며 최대 횡오차 약 0.0274m. 실제 성능으로 해석하지 않는다.

## 현 환경의 한계와 남은 필수 항목
이 개발 환경에 ros2/gz 실행 파일이 없어 colcon, Gazebo, SLAM 실행을 검증하지 못했다.
아래는 TODO이며 토요일 목표 전체 완료가 아니다.
1. 공식 Pinky Gazebo 모델·bridge와 실제 토픽·frame 확인.
2. 정찰 벽 추종을 ROS scan 입력에 연결하고 slam_toolbox 지도 생성.
3. loop closure 후 지도에서 충돌 여유를 검사한 경로 생성.
4. localization pose를 경로 frame으로 변환하고 tracking/pose에 연결.
5. 로컬 최종 guard와 모터 watchdog 연결 및 통신 단절 정지 확인.
6. Gazebo에서 정찰부터 3랩까지 통합 시험.
7. 11/21 실물 odom/scan/camera/TF 기록, 속도별 정지 거리 측정, 저속 1대 완주.

## 지금 실행
```bash
python3 scripts/check_core.py
python3 scripts/check_guard.py
python3 scripts/guide_smoke.py
python3 scripts/simulate_laps.py --seeds 10
```

## ROS 연결 시험 계약
ROS 환경에서 colcon 빌드 후 tracking_node를 실행한다. JSON 경로는
`{"frame_id":"map","points":[[0,0],[2,0],[2,1],[0,1]]}` 형식이다.
이는 형식 설명용 경로이며 실제 트랙으로 사용하지 않는다. 마지막 점에 첫 점을 반복하지 않는다.

```bash
ros2 run pinky_gp_navigation tracking_node --ros-args -p path_file:=/absolute/verified_path.json
```

- tracking/pose: geometry_msgs/PoseStamped, JSON과 같은 좌표계. TF 변환은 upstream 담당.
- tracking/enable: std_msgs/Bool. 기본 정지. 새 enable 이후 새 pose 필요.
- candidate/nav: geometry_msgs/Twist. 최종 모터 토픽으로 직접 remap하지 않는다.
- tracking/status: std_msgs/String JSON.
- speed 등 기본값은 합성 시험용이며 실물 측정값으로 교체한다.
- 위치 오류로 disable되면 원인 해결 후 재허용이 필요하다. 완료 상태 해제는 노드 재시작으로 한다.
- localization의 ROS 시간은 노드와 같은 use_sim_time 설정이어야 한다.

## 4명 다음 행동
A: Gazebo 센서/정찰/SLAM, B: 영상·센서 실제 데이터 수집과 시간 확인,
C: 후보 명령과 상태/랩 로그 검토, D: 최종 guard·watchdog와 실행 연결.
현장 VERIFIED는 변경하지 않았다. evidence의 운동학 결과와 실물 시험 결과를 구분한다.
