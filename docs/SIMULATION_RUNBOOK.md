# Pinky GP 단독 주행 시험 가이드

토요일 첫 목표는 Pinky Pro 한 대가 사전 등록 지도에서 출발해 스스로 3랩을 돌고 멈추는 것이다. 지도 제작은 경기 전에 한 번 수행한다. 경기 중 새로 나타난 물체는 매 스캔마다 판단한다. 경기 결과와 각 시험의 실패 원인은 실행별로 보관한다.

## 1. Ubuntu 24.04 · ROS 2 Jazzy에서 처음 한 번

아래는 팀원이 기존 작업 파일을 건드리지 않고 시험용 워크스페이스를 만드는 절차다. 이미 같은 이름의 워크스페이스가 있으면 해당 체크아웃에서 시작한다. ROS 2 Jazzy가 설치된 PC에서 실행한다.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y git python3-colcon-common-extensions libgl1-mesa-dri \
  ros-jazzy-ros-gz ros-jazzy-xacro ros-jazzy-robot-state-publisher \
  ros-jazzy-nav2-map-server ros-jazzy-nav2-amcl ros-jazzy-nav2-lifecycle-manager \
  ros-jazzy-slam-toolbox ros-jazzy-rosbag2

mkdir -p ~/pinky_gp_sim_ws/src
cd ~/pinky_gp_sim_ws/src
git clone --branch feat/registered-map-weekday-validation https://github.com/BBANG-JUN01/pinky_RACE_team5.git
git clone https://github.com/pinklab-art/pinky_pro.git
git -C pinky_pro checkout --detach 014a09f289e6988894fbffde2624fdb1e257815b

cd ~/pinky_gp_sim_ws
colcon build --base-paths src/pinky_RACE_team5/src src/pinky_pro/pinky_description \
  --packages-up-to pinky_gp_bringup --symlink-install --cmake-args -DBUILD_TESTING=OFF
source install/setup.bash
cd src/pinky_RACE_team5
```

다음 날 새 터미널에서는 `source ~/pinky_gp_sim_ws/install/setup.bash` 후 팀 저장소 디렉터리로 이동한다. 이 빌드는 공식 로봇 모델과 팀 ROS 패키지 5개를 설치한다. 시험 프로그램은 저장소의 `scripts/`에 있다.

## 2. 첫 실행과 전체 검증

**눈으로 한 번 보기**. 터미널 하나에서 다음을 실행하면 Gazebo가 뜨고, 지도·AMCL·센서 준비가 끝나면 시험기가 출발시킨다. 로봇이 같은 방향으로 결승선을 세 번 통과하고 정지하면 종료한다. GPU 없는 PC나 원격 환경에서는 `--gui`를 생략한다.

```bash
python3 scripts/run_single_trial.py --backend gazebo --case clean --gui --bag
```

**전체 시험**. 아래 명령은 회귀 시험, 광선 기반 장애물 시험, 실제 ROS 노드 시험, Gazebo 시험, 최종 주행 기록의 SLAM 지도 생성, 해당 지도로 다시 3랩을 순서대로 진행한다. 처음 실패한 단계에서 종료 코드 1을 반환한다. 결과 폴더마다 고유 시각을 쓰므로 재실행 결과를 비교할 수 있다.

```bash
python3 scripts/validate_racing.py --through gazebo --reuse-slam-map
```

| 실행 범위 | 명령 | 확인할 결과 |
|---|---|---|
| ROS 설치 전 | `python3 scripts/validate_racing.py --through software` | 회귀 시험과 8개 시드 × 3가지 센서 시나리오 |
| ROS·AMCL 집중 | `python3 scripts/validate_racing.py --through ros --reuse-slam-map` | ROS 토픽, TF, 서비스, AMCL, 최종 정지, SLAM 지도 재사용 |
| Gazebo 한 조건 재현 | `python3 scripts/run_single_trial.py --backend gazebo --case cone --bag` | 주행 시작 후 삽입한 장애물 우회와 완주 |
| 관제 정지·깃발 | `python3 scripts/run_single_trial.py --backend gazebo --case rules --bag` | 속도 상한, 사람 이벤트, 페널티, 레드 종료 |
| 시계 단절·체커 | `python3 scripts/run_single_trial.py --backend gazebo --case watchdog --bag` | 일시정지 중 0출력, 재개 후 다음 결승선에서 종료 |

같은 PC에서 동시에 두 시험을 돌릴 때는 다른 `--domain`을 준다. 기본은 82다. 시험기는 Gazebo 통신 파티션을 실행마다 만든다. `--seed`는 광선 기반 ROS 시험의 센서 잡음에 적용된다. Gazebo 반복은 모델을 새로 띄워 독립적으로 출발시킨다.

## 3. 무엇이 실제로 연결되는가

Gazebo가 공식 Pinky Pro 로봇의 차동구동·바퀴 오도메트리와 360° GPU LiDAR를 실행한다. ROS 브리지가 `/scan`, `/odom`, `/clock`, TF를 전달한다. AMCL이 사전 등록 지도와 스캔을 맞춰 위치를 추정한다. 컨트롤러는 스캔 시각의 `map → base_footprint`와 `map → rplidar_link`를 조회한다. 공식 로봇의 라이다 축이 반 바퀴 돌아간 장착 자세도 이 변환에 포함된다.

- 추종기는 폐곡선의 전방 목표점으로 Pure Pursuit 곡률을 계산한다. 차동구동에 맞춰 `w = v × 곡률`로 변환한다. 코너의 각속도·횡가속 상한, 제동거리, 차량 외곽을 적용한다.
- 0.74 m 전방의 중심선과 좌우 우회선을 정적 지도 및 최신 스캔과 대조한다. 한쪽을 선택하면 최초 우회 곡선을 유지한다. 경로와 실제 명령의 제동 궤적 중 하나라도 막히면 정지한다. 새 위치를 메우기 위해 정적 지도를 다시 저장할 필요가 없다.
- 최종 가드가 확인한 후보만 `/gp/sim_cmd_vel`로 나간다. 브리지가 이 명령을 Gazebo의 `/cmd_vel`로 넘긴다. 추정 위치와 독립인 `/gp/truth`는 시험기가 결승선과 여유거리를 재는 데만 쓴다.
- `/gp/status`에 현재·직전·베스트 랩과 전체 랩 기록이 있다. 완주 시 마지막 랩 시간이 고정된다. `rules`의 사람과 깃발은 관제 이벤트를 주입해 로봇 반응을 검증한다. 실제 영상 분류 정확도와 LCD·LED 장치 출력은 별도 현장 시험 항목이다.
- `ros_fixture`는 실제 ROS 노드와 AMCL, TF, 서비스, 가드를 구동한다. 센서 발생기와 운동 모델은 팀의 광선 기반 모델이다. Gazebo는 공식 로봇 모델과 Gazebo 엔진을 사용한다.

## 4. 합격 판정

| 시험 | 조작 | 합격 증거 |
|---|---|---|
| clean 2회 | 빈 트랙에서 서로 다른 실행으로 출발 | 회당 순서 있는 3랩, 모델 위치로 독립 판정한 3랩, 결승선 부근 정지 0.5초 |
| cone | 출발 뒤 경로에 작은 사각 장애물 투입 | 3개 이상의 우회 상태 표본, 차량 외곽 여유거리 0 이상, 1랩 완주 |
| barrier | 차로 전폭을 막았다가 시험기가 제거 | 물체 앞 정지와 0출력 1초 연속, 제거 후 스스로 주행·완주 |
| rules | 옐로 → SC → 그린 → 사람 등장·해제 → 정지 페널티 → 레드 → 그린 | 제한 주행 0.12/0.09 m/s, 그린 복귀, 정지 계시, 레드 이후 정지 유지. Gazebo에서는 카메라 이미지 수신도 확인 |
| watchdog | 주행 중 세계 시각을 일시정지했다가 재개, 이후 체커 이벤트 | 실제 시간 1초 안에 최종 0출력, 새 센서로 재개, 3랩 설정에서도 다음 유효 결승선에서 종료 |
| SLAM 재등록 | 마지막 정상 주행 bag을 독립 도메인에서 재생 | 새 PGM/YAML과 점유 셀 생성, 지정한 새 지도에서 3랩 및 독립 완주 판정 |

랩 판정은 전진 체크포인트 세 곳과 결승선을 순서대로 요구한다. 시작선 근처를 앞뒤로 오가는 동작은 랩이 되지 않는다. 시험기는 마지막 모델의 종방향 위치 −0.08~0.15 m, 횡위치 절댓값 0.31 m 이하를 확인한다. **콘을 피해 바깥 라인으로 결승선을 통과하는 것도 유효하다.** 여유거리는 모델 중심에서 벽·동적 물체까지의 거리에서 시험용 반경 0.13 m를 뺀 값이다. Gazebo 접촉 센서의 충격량과 실물 범퍼 접촉은 별도 측정량이다.

## 5. 실패하면 이 순서로 확인

먼저 실행이 출력한 경로의 `summary.json`에서 실패한 단계 이름을 찾는다. 개별 실행의 `result.json`은 마지막 상태·센서 표본 수·모델 위치·여유거리·랩타임, `events.jsonl`은 상태가 바뀐 시각, `launch.log`는 실제 노드 오류를 담는다. `--bag`을 주면 ROS 원본도 남는다. 같은 조건의 한 번짜리 명령으로 재현한 뒤 수정하고 전체 시험을 다시 실행한다.

| 마지막 증상 | 먼저 확인 | 수정 후 재시험 |
|---|---|---|
| `Package ... not found` | 새 터미널의 `echo "$ROS_DISTRO"`, `ros2 pkg prefix pinky_gp_bringup`, `ros2 pkg prefix pinky_description` | 1절 빌드 및 source → clean |
| `WAIT_MAP` / `REGISTERED_PATH_BLOCKED` | `map.yaml`의 이미지 상대경로·해상도·원점, 지도와 경로 좌표계, unknown/벽과 차체 반경의 교차 | 등록한 지도와 경로를 같은 버전으로 맞춘 뒤 clean |
| `WAIT_AMCL` / `WAIT_TF` 지속 | 같은 ROS 도메인에서 `ros2 run tf2_ros tf2_echo map base_footprint`, `ros2 run tf2_ros tf2_echo base_footprint rplidar_link` | 시뮬레이션 시각과 프레임을 맞춘 뒤 clean. 기동 직후 짧은 대기는 정상 |
| `SCAN_TIMEOUT` / `BLIND_SCAN` / `ODOM_TIMEOUT` | `ros2 topic hz /scan`, `ros2 topic hz /odom`, `ros2 topic echo /clock --once`, 스캔의 타임스탬프·각도·거리범위 | 잘못된 브리지나 렌더러를 수정하고 watchdog → clean |
| 창이 검거나 GPU LiDAR가 비어 있음 | `launch.log`의 EGL/Ogre 오류, Gazebo 서버 생존, 소프트웨어 렌더러 설치 | `LIBGL_ALWAYS_SOFTWARE=1 python3 scripts/run_single_trial.py --case clean` |
| `getifaddrs` / `Operation not permitted` 후 Gazebo 종료 | 프로세스가 로컬 전송 인터페이스를 열 수 있는지 확인 | Ubuntu PC 또는 제공된 GitHub Actions 실행. ROS만 진단할 때 `--through ros` |
| 콘에서 `NO_CLEAR_LANE` | 전폭 차단인지, 실제 남은 차폭, 궤적이 어느 쪽으로 바뀌는지, 최소 여유거리 | 콘 하나로 재현. 후방 레이저 장착 TF와 우회선 수용 조건부터 확인. 전폭 차단에서는 정지가 합격 |
| `LOCALIZATION_JUMP` / `WRONG_HEADING` | AMCL 초기 자세와 첫 경로점 접선, 시각 재설정, 서로 다른 등록 버전 | 초기 위치·방향을 바로잡고 새 경기로 시작 |
| 랩 수 불일치 | `events.jsonl`의 truth_gate 순서, 중앙선을 가로지른 방향, 최종 x/y, 멈춘 시각 | 완주선을 가로선으로 평가하고 실제 궤적과 체크포인트를 대조 |
| `rules` / `watchdog` 실패 | `/gp/event`의 경기 ID·수신 시각·대상, 최종 명령과 odom이 함께 0이 된 시점 | 해당 case 단독 → 전체. RED 종료 뒤에는 새 경기 실행 |
| 지도 저장 실패 | SLAM bag의 `/scan /tf /tf_static`, 시뮬레이션 bag의 `/clock`, `mapping.log`의 lifecycle과 map 수신 | 비어 있는 새 출력 폴더로 동일 bag 재생 |

자동 실행 중 다른 터미널에서 관찰하려면 `source ~/pinky_gp_sim_ws/install/setup.bash`, `export ROS_DOMAIN_ID=82 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`를 먼저 적용한다. `ros2 topic echo /gp/status --once`에서 한 랩의 상태와 계시를 볼 수 있다.

## 6. 팀의 SLAM 지도를 다시 사용할 때

```bash
python3 scripts/register_from_bag.py /절대경로/bag /절대경로/새등록폴더
python3 scripts/run_single_trial.py --case clean --map-file /절대경로/새등록폴더/map.yaml
```

두 번째 명령의 자동 채점기는 제공된 트랙 형상 전용이다. 다른 트랙에서는 그 트랙의 월드·지도·경로를 지정하고 결승선 위치도 해당 트랙에 맞춰야 한다. 제공된 로봇은 월드 원점에서 +x 방향으로 출발한다. 외부 경로 JSON은 `frame_id`가 `map`이고, `points`가 m 단위의 순서 있는 폐곡선 좌표다. 마지막에 첫 점을 중복해 넣지 않는다.

```bash
ros2 launch pinky_gp_bringup single_gazebo.launch.py gui:=true \
  world_file:=/절대경로/track.sdf map_file:=/절대경로/map.yaml path_file:=/절대경로/path.json
```

직접 launch한 경우 같은 ROS 환경의 다른 터미널에서 `ros2 service call /gp/start std_srvs/srv/Trigger '{}'`로 출발한다. 자동 시험 스크립트가 이미 실행 중인 경우에는 스크립트가 이 서비스를 호출한다.

## 7. 토요일 실물 진행 순서

| 시간 | 팀 작업 | 다음 단계로 넘어갈 조건 |
|---|---|---|
| 09:00–10:00 | A·B가 LiDAR/odom/TF와 장착 방향 기록, C·D가 모터 명령 소유자와 운영자 정지 확보 | 바퀴를 띄운 상태에서 전진 부호, 좌회전 부호, 통신 단절 0출력 확인 |
| 10:00–12:00 | 실제 트랙을 저속 수동 주행해 SLAM 지도 저장. 그리드 원점·방향과 주행점을 같은 좌표계로 등록 | 저장한 파일로 위치 추정 재시작, 벽·경로·차체 여유 확인 |
| 13:00–15:00 | 직선 속도를 단계적으로 올리고 제동거리·명령 지연·좌우 코너 이탈을 각각 반복 측정 | 실측 결과로 안전 속도·정지거리·회전 한계 설정 |
| 15:00–17:00 | 별도 실물 모터 어댑터와 독립 정지 경로 연결 후 저속 단독 3랩. 콘·차단벽은 분리 시험 | 독립 계시와 3랩 일치, 접촉과 운영자 개입 기록 |
| 17:00–19:00 | 단독 기준을 재현한 뒤 두 번째 로봇의 네임스페이스·TF 분리와 상호 정지부터 시험 | 두 로봇 명령이 교차하지 않음. 이후 나란한 그리드·구간 DRS·추월로 진행 |

실물 모터와 물체·사람 YOLO, 출발등/깃발 영상 판독, LED/LCD 실장, 두 대 간 DRS·추월 통합에는 각 장비의 독립 검증이 남아 있다. 아이템·코너 보상은 최후순위다. 실물 속도 기준은 토요일 측정에서 확정한다.

공식 모델 [Pinky Pro](https://github.com/pinklab-art/pinky_pro/tree/014a09f289e6988894fbffde2624fdb1e257815b) · 알고리즘 참고 [F1TENTH Pure Pursuit](https://f1tenth-coursekit.readthedocs.io/en/stable/assignments/labs/lab6.html)
