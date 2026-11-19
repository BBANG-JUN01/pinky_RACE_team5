# 자동 주행선 최적화 → 실물 → 두 대 경쟁

## 구현 범위와 현재 판정

지도상의 기준 폐곡선을 좌우로 부드럽게 이동시키며 예상 랩타임을 줄인다. 차체 반경으로 확장한 벽·미확인 영역을 경로의 **모든 선분**에서 검사한다. 곡률, 각속도, 횡가속도, 좌우 바퀴 속도, 가속 및 제동 한계로 속도 프로파일을 계산한다. 전역 최단시간이나 실물 최적 성능을 보장하는 알고리즘은 아니다. 최적화는 출발 전 실행하며, 주행 중에는 기존 센서 기반 회피/정지를 사용한다.

기존 기준 경로가 등록 지도에서 막혀 있으면 최적화를 거부한다. SLAM 재등록으로 좌표계가 이동한 경우 기준 경로를 새 지도 좌표로 다시 등록해야 한다. 자동 정합은 구현하지 않았다. 이전 Gazebo 테스트에서 SLAM 지도 재사용이 이 문제로 실패했으므로, 이 항목을 해결 완료로 취급하지 않는다.

단순 운동학 비교(공식 Gazebo/실물 결과 아님): 기준 정상 랩 약 30.41초, 후보 약 25.30초. 최소 벽 여유는 각각 약 0.213m / 0.086m. 이득과 여유 감소를 같이 판단한다. `Racing line A-B validation` CI가 공식 모델의 센서·AMCL·물리 주행으로 별도 검증한다. 공식 Gazebo A/B CI는 아래 기록처럼 통과했다. 실물 채택은 별도 검증한다.

## 1. 온라인 준비

저장소 루트, ROS Jazzy 워크스페이스 빌드 및 source 후 실행한다.

```bash
python3 scripts/check_core.py
python3 scripts/compare_racelines.py
python3 scripts/verify_optimized_sensors.py
python3 -c "from pinky_gp_navigation.track_fixture import write_track; from pathlib import Path; write_track(Path('/tmp/ab_track'))"
python3 scripts/optimize_raceline.py --map /tmp/ab_track/map.yaml --reference /tmp/ab_track/path.json --profile src/pinky_gp_bringup/config/racing_sim.json --offset 0.20 --output /tmp/ab_track/optimized.json
python3 scripts/run_single_trial.py --case clean --limits-file src/pinky_gp_bringup/config/racing_sim.json --output log/ab/baseline
python3 scripts/run_single_trial.py --case clean --limits-file src/pinky_gp_bringup/config/racing_sim.json --path-file /tmp/ab_track/optimized.json --output log/ab/optimized
python3 scripts/score_raceline_trials.py log/ab/baseline log/ab/optimized
```

반복 비교 시 매번 새 출력 폴더를 사용한다. 판정기는 폴더당 1개 결과를 요구한다. 최소 3랩, 충돌 없음, 독립 체크포인트 일치, 2·3랩 평균 단축이 통과 조건이다. 최적화 실패는 기준 경로로 복귀하여 진단한다. map.yaml/PGM만으로 물리 시뮬레이터가 생성되는 것은 아니며, 위 fixture에는 별도 대응 SDF가 있다.

## 2. 토요일 09:00–19:00

| 시간 | 담당/작업 | 통과 기준 |
|---|---|---|
| 09–10 | 1: 하드웨어/드라이버, 2: 속도·제동 기록, 3: 지도, 4: 로그/비상정지 | 센서/TF 정상, 단일 모터 명령 발행자, 정지 시험 |
| 10–11:30 | 차체/바퀴 간격, 저속부터 실제 바퀴속도·가감속·지연·선회 측정 | 측정 CSV 또는 기록 파일, 보수적 프로파일 |
| 11:30–13 | 실제 트랙 SLAM 저장, map 좌표 기준선 등록, AMCL 초기화 | 전체 경로 충돌 검사 통과, 저속 1랩 |
| 13–14 | 단독 기준 경로 3랩 반복 | 무충돌/오인식 없는 완주 |
| 14–15:30 | 실물 프로파일로 후보 생성, 같은 조건 A/B | 후보 3랩 반복 완주, 랩타임과 최소 여유 비교 |
| 15:30–17 | 두 번째 로봇 별도 측정/단독 완주, 두 도메인 연결 | 각 로봇 정지/출발/로그 독립 |
| 17–18 | 간격을 둔 두 대 동시 주행 → 가까운 추종 | 상대 감지 시 감속/정지, 접촉 없음 |
| 18–19 | 반복 경기/로그 저장/속도 확정 | 실패 원인 기록, 최종 설정 고정 |

단독 완주가 안 되면 두 대 시험 시간도 단독 튜닝에 사용한다. 플래그·아이템 신규 기능은 이 일정의 필수 조건이 아니다.

## 3. 실물 측정값 적용

`config/racing_hardware.example.json`의 값은 **측정값이 아닌 예시**다. 로봇별 파일로 복사하고 모든 물리값을 측정에 따라 수정한다. `radius_m`에는 장착물까지 포함한 차체 외접 반경과 필요한 여유를 반영한다. `limits.margin`은 정지거리 여유이며 지도 차체 확장 반경과 별도다. 충분히 보수적인 제한부터 시작한다. 측정 완료 후에만 `verified: true`, `measurement_record`에 실제 기록 경로를 설정한다. 이 필드는 사람의 확인 선언이며 파일의 내용까지 자동 검증하지는 않는다.

프로파일 변경 후 후보를 다시 생성한다. 실행 시 최적화 파일의 프로파일 해시가 다르면 거부한다. 지도 변경 시에도 다시 생성한다. 출력 provenance에 원본 지도/이미지 해시가 저장되며, 런타임은 실제 수신 지도에서 경로 전체 충돌 검사를 다시 한다. 지도 파일 해시의 런타임 일치 검사는 별도로 구현하지 않았다.

```bash
python3 scripts/optimize_raceline.py --map /absolute/maps/map.yaml --reference /absolute/maps/reference.json --profile /absolute/profiles/A.json --offset 0.10 --output /absolute/maps/A_optimized.json
```

`reference.json`: `{"frame_id":"map","points":[[x,y],...]}`. 최소 16개 순서 있는 점, 마지막에 시작점을 중복하지 않는다. 첫 점과 진행 방향이 출발 그리드다. 자동 중심선 추출/지도 좌표 정합은 포함하지 않는다.

공식 실물 bringup으로 /scan, /odom, odom→base_footprint→rplidar_link TF를 먼저 실행한다. 기존 Nav2 controller/teleop 등 /cmd_vel 발행자는 중단한다. 아래 launch가 map_server와 AMCL을 시작하므로 중복 실행하지 않는다. 실제 모터 토픽 타입은 geometry_msgs/msg/Twist여야 한다. RViz에서 실제 위치/방향으로 2D Pose Estimate를 설정한다.

```bash
export ROS_DOMAIN_ID=41
ros2 launch pinky_gp_bringup hardware.launch.py limits_file:=/absolute/profiles/A.json map_file:=/absolute/maps/map.yaml path_file:=/absolute/maps/A_optimized.json robot_id:=A race_id:=race1
```

별도 터미널도 같은 ROS 환경과 도메인을 사용한다.

```bash
export ROS_DOMAIN_ID=41
ros2 topic echo /gp/status
# READY와 실제 위치를 확인한 뒤 별도 터미널에서 출발
ros2 service call /gp/start std_srvs/srv/Trigger '{}'
# 운영자 정지; false로 해제하면 새 유효 명령으로 재개 가능
ros2 service call /gp/stop std_srvs/srv/SetBool '{data: true}'
```

센서/명령 정체는 guard가 정지시킨다. 하지만 guard 프로세스 자체/네트워크가 죽었을 때의 모터 정지는 하위 드라이버/펌웨어 cmd_vel timeout에 의존한다. 실물에서 이 timeout과 물리 비상정지를 먼저 확인한다.

## 4. 두 대 경쟁 적용 방식과 한계

A는 ROS_DOMAIN_ID=41, B는 42로 분리한다. 각 로봇의 공식 bringup, race launch, RViz, start/stop 및 rosbag 모두 자기 도메인을 사용한다. B에는 `robot_id:=B`와 B 측정 프로파일/최적화 경로를 준다. 도메인 분리로 같은 /scan, /tf, /cmd_vel 이름이 섞이지 않는다. 원격 PC 사용 시 LOCALHOST discovery 제한을 해제하고 실제 연결을 확인한다.

첫 시험은 동일 진행 방향으로 충분한 간격을 둔 추종 주행이다. 두 로봇이 각자 인식한 상대는 LiDAR 장애물로 처리한다. 한 도메인에서 다른 로봇의 명령/위치를 직접 읽지 않는다. 측면 그리드 동시 출발은 각각의 시작 위치에 맞는 기준선을 만들고 단독 검사부터 진행한다. 시작점이 틀린 경로를 억지로 재사용하지 않는다.

**현재 제공하는 수준은 두 로봇 독립 제어와 센서 기반 회피를 활용한 경쟁 시험 준비다.** 공유 순위 서버, 엄밀한 동시 출발, 로봇 ID 인식, 상호 양보/추월 전술, 같은 Gazebo 월드 두 로봇 통합 시험은 아직 없다. 따라서 접촉 없는 추월 경쟁 완료로 표기하지 않는다. 자동 추월 성공을 전제로 속도를 올리지 않는다. 한 대씩 3랩 완주 → 간격 둔 두 대 → 가까운 추종 → 넓은 구간에서 회피 순서로 검증한다.

## 문제별 조치

| 현상 | 조치 |
|---|---|
| 경로 막힘/미확인 영역 | 지도 origin/resolution/경로 좌표 일치 확인; 새 지도에 기준선 재등록 |
| 코너 진입 후 멈춤/벽 접근 | offset을 줄여 새 후보 생성; 실측 각속도·휠속도·제동 설정 확인 |
| 후보가 더 느림 | 후보 채택 보류, 기준 경로 유지; 비교 로그 확인 |
| READY 안 됨 | /scan·/odom 시각, TF, AMCL 공분산 및 초기 위치 확인 |
| 두 대 명령 섞임 | 두 로봇과 각 터미널의 ROS_DOMAIN_ID 재확인 |
| 상대 앞에서 교착 | 정지 유지 후 운영자 재배치; 협력 추월 미구현 상태로 기록 |

두 도메인에 연결되는 운영 PC에서는 아래 도구로 출발/정지 요청을 병렬 발행할 수 있다. 한 대라도 출발 승인이 실패하면 두 대 모두 정지를 요청한다. 통신 단절 시 원격 정지 응답은 보장되지 않으므로 각 로봇의 독립 비상정지는 유지한다. 출발 시각 동기화나 판정 서버를 대신하는 기능은 아니다.

```bash
python3 scripts/duel_control.py start --domains 41 42
python3 scripts/duel_control.py stop --domains 41 42
```

추가 검증: 640광선, 거리 노이즈 표준편차 0.02m, 서로 다른 seed 3회에서 후보 경로가 각 3랩 완주했다. 최소 벽 여유 0.0853m 이상이었다. 이 시험은 raycast + 운동학 모델이며 Gazebo와 구분한다. 로컬 단위/회귀 테스트는 84개 통과했다.

## 2026-11-19 공식 Gazebo 검증 결과와 남은 제한

[시험 실행 로그](https://github.com/BBANG-JUN01/pinky_RACE_team5/actions/runs/44444545644), 주행 코드 커밋 a1f31fe11f5b477a40d5ac18c3d4a8fafe68ae04 기준.

| 항목 | 기준 경로 | 최적화 후보 |
|---|---:|---:|
| 1랩 | 30.786초 | 25.850초 |
| 2랩 | 30.310초 | 25.346초 |
| 3랩 | 30.380초 | 25.348초 |
| 2·3랩 평균 | 30.345초 | 25.347초 |
| 최소 벽 여유 | 0.1936m | 0.0748m |

동일 제한값, 공식 Pinky 모델, LiDAR/odom/AMCL 사용, 별도 world truth로 3랩 및 충돌 여부를 판정했다. 약 16.5% 단축은 이 트랙에서의 1회 A/B 결과이며 실물/다른 트랙 일반화 결과가 아니다. 후속 커밋은 운영 도구·노이즈 시험·문서 추가이며 이 주행 제어 코드는 동일하다.

**미해결: 최적화 경로 + 콘 우회 조합.** 추가 raycast 시험 2회에서 충돌 없이 NO_CLEAR_LANE 정지했으나 완주하지 못했다. 막는 장애물 제거 후 재출발은 같은 시험에서 통과했다. 최적화 경로의 콘 우회나 움직이는 상대 추월은 검증 완료가 아니다. 재현:

```bash
python3 scripts/verify_optimized_sensors.py --scenario cone --seeds 2
```

이 명령은 현 버전에서 실패 코드를 반환하는 알려진 제한이다. 단독 타임어택은 최적화 후보를 시험할 수 있지만, 두 대 추월 경쟁에서는 기준 경로부터 별도로 검증한다. 자동 우회가 보장된다고 가정하고 최적화 경로로 두 대를 가까이 출발시키지 않는다. 두 대 도메인/운영 도구 구현과 두 대 주행 통합 검증 완료를 구분한다. PC와 로봇의 시각도 동기화해 센서 freshness 검사를 통과시킨다.
