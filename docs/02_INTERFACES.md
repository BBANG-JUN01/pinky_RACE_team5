# 공통 인터페이스와 시간 계약

아래 토픽 이름은 프로젝트 내부 계약 제안이다. 제조사 실제 센서와 모터 이름은 S00에서
hardware_inventory.example.yaml을 복사해 확인한다. Twist와 TwistStamped를 임의 가정하지 않는다.

| 프로젝트 토픽 또는 서비스 | 형식 | 발행 또는 서버 | 소비자 |
|---|---|---|---|
| /gp/race/control | RaceControl | race_manager | 전체 |
| /gp/race/submit_command | SubmitCommand.srv | race_manager | operator_server·인식 어댑터 |
| /robot_a/gp/status | RobotStatus | robot_health | race·behavior·관제 |
| /robot_a/gp/detection | Detection | perception | behavior·signal |
| /robot_a/gp/motion | MotionStatus | behavior | guard·display·관제 |
| /robot_a/gp/progress | RaceProgress | progress_manager | 관제·display·DRS |
| /robot_a/gp/effects | EffectState | race | behavior·display |
| /robot_a/gp/stop_state | StopState | guard | 관제·display |
| /gp/map_ready | MapReady | map_finalize | 지도 로더·관제 |
| /robot_a/gp/cmd_vel/recon | 현장 검증한 명령 형식 | wall_follower | arbiter |
| /robot_a/gp/cmd_vel/grid | 같은 명령 형식 | grid_manager | arbiter |
| /robot_a/gp/cmd_vel/nav | 같은 명령 형식 | Nav2 | arbiter |
| 로봇별 실제 motor 토픽 | 현장 확인 | 최종 guard만 | 제조사 base |

robot_b는 동일 계약을 사용한다. 전역 원시 센서 토픽과 프레임을 공유하지 않는다.
공통 map 아래 robot_a/odom → robot_a/base_link 등의 프레임 트리를 검증하며,
frame 이름은 실제 URDF와 일치시킨다. TF remap과 프레임 prefix는 다른 문제다.

## 시간과 이벤트

- header.stamp는 원래 측정/촬영 시각이다. 수신 시각은 timeout용으로 별도 기록한다.
- 중앙 단조 증가 시각으로 경기 시간을 계산한다. 컴퓨터별 monotonic 값은 직접 비교하지 않는다.
- ROS stamp 비교는 PC·로봇 시각 동기화 검증 후 사용한다. simulation에서는 use_sim_time을 통일한다.
- GREEN은 현재 제한의 시작보다 새로운 유효 영상 이벤트일 때만 적용한다.
- RED는 승인된 경기 종료 이벤트이며 같은 race의 최신 상태에 유지한다.
- 중복 command_id 재전송은 결과를 재확인하되 실행하지 않는다. 서비스 accepted는
  명령 접수이며 실제 정지 완료는 RobotStatus와 MotionStatus로 별도 확인한다.
- 화면의 0.01초 표시는 같은 수준의 계측 정확도를 보장하지 않는다.

## QoS와 데이터 신선도

센서는 발행자와 맞는 SensorData QoS부터 확인한다. 경기 상태 snapshot은 reliable과
transient_local 후보를 사용하되, 재접속 때 stale snapshot으로 출발하지 않도록
race_id, revision과 freshness를 검사한다. 이벤트는 명령 ID·ack로 중복을 관리한다.
최종 구동 명령은 오래된 명령을 보관·재생하지 않는다. depth와 deadline, timeout 수치는
지연 분포 측정 후 확정한다. 모든 토픽에 무조건 reliable을 적용하지 않는다.

## 설정 소유권

하드웨어 설정은 D, 주행/경계 설정은 A, 모델/검출은 B, 경기/DRS는 C가 검토한다.
새 경기마다 지도와 경로 manifest의 해시를 대조한다. MapReady의 artifact_uri는 전송 완료를
뜻하지 않는다. B에 파일을 전달하고 해시와 로딩 결과를 확인한 뒤 준비 완료로 처리한다.
