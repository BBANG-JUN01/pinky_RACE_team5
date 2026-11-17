# 실제 구현 상태 · v0.2

기획서의 기능 완료와 순수 Python 가이드 구현을 구분한다.

| 영역 | 구현된 부분 | 남은 부분 |
|---|---|---|
| core | 경기 제한/정지/DRS/랩타이머/화면 우선순위 | ROS adapter의 권한·측정 시각 검사 |
| guard | 제어권 선택, timeout, 유한값 검사, 속도 제한 | 센서 callback, motor publisher, base watchdog |
| recon | 좌측 벽 P 제어, 복귀 조건, 파일 해시 manifest | PID 튜닝, SLAM, 중심선 추출, footprint 검사 |
| navigation | 폐곡선 길이·근방 투영, 정렬 제어, goal 상태 계약 | Nav2 action client, 경로 충돌 검사, TF, 재계획 |
| perception | 검출 결과 필터, 보정 후 거리 집계, 출발등 순서, 표식 선택 | YOLO 모델/영상 입력, LiDAR 투영, 깃발 인식 |
| race | 생애 FSM, 랩 스냅샷/순위, 연속 정지 페널티 | 실제 gate 교차 판정, 이벤트 버스, 시각 동기화 |
| behavior | 추월 FSM, 제한·앞차·곡률 속도 상한 | 앞차 식별, SC 순서 고정, 후보/합류 경로 생성 |
| display | LED 의미 및 LCD 현재/직전/베스트 랩 프레임 | 실제 장치 출력, 비동기 큐, 데이터 동기화 |
| dashboard | 명령 종류·페널티 입력 검증, 고유 ID | HTTP/Web UI, 인증, ROS 서비스와 영속 로그 |
| interfaces | msg/srv 초안 | rosidl 컴파일과 ROS 통합 시험 |
| bringup | 설정 파일과 장비 조사 양식 | 실제 launch 구성, remap과 상태 검사 |
| 선택 기능 | S12 요구·구현 순서 | 아이템/코너 보상 코드 전체 |

19개 기능 모듈은 `--demo`로 실행 가능하다. **이 함수들이 서로 연결된 ROS 노드는 아직 없다.**
Nav2/모델/지도 저장/표시 드라이버를 더미 성공으로 처리하지 않는다.

현장 작업 52개 모두 TODO. 자동 테스트 통과는 현장 VERIFIED로 올리지 않는다.
