# 제공 코드 검증 · 2026-11-17

| 항목 | 결과 | 범위 |
|---|---|---|
| `python3 scripts/check_core.py` | 45개 통과 | core 20 + guide 25 |
| `python3 scripts/guide_smoke.py` | 19개 데모 통과 | JSON 직렬화, Python AST, package.xml 파싱 |
| `python3 scripts/replay_demo.py` | 통과 | RED 이후 GREEN에도 정지 유지 |
| `python3 scripts/race_scenario.py` | 통과 | 합성 준비/출발/SC/페널티/체커/표시 연결 |
| `python3 scripts/export_progress.py` | 52개 출력 | Markdown, UTF-8 CSV |
| ROS 2/colcon/rosidl | 미실행 | 이 환경에 ROS 설치 없음 |
| 실제 센서/SLAM/Nav2/YOLO/모터/LED/LCD | 미연결·미검증 | 현장 단계 S00~S11에서 검증 |

자동 테스트는 실패 조건도 포함한다: 잘못된 제어권, 미래/오래된 명령, 누락 센서,
정찰 이탈 없이 복귀, Nav2 취소 ACK 이전 재요청, 모호한 거리, 중복 마커,
출발등 가림/순서 오류, 잘못된 경기 전이, 중복 명령, RED 이후 GREEN,
체크포인트 순서, stale odom의 페널티 계시, SC 중 추월 취소, 사람 정지 중 DRS, stale 화면.

`evidence/software_validation.txt`에 이번 실행 결과를 보관했다.
현장 작업 52개는 모두 TODO이며 단위 테스트 통과를 실물 기능 완료율로 계산하지 않는다.

알려진 제한: P 벽 추종은 복잡한 코너 탈출을 구현하지 않는다. 경로는 주어진 점열을
계산할 뿐 지도에서 중심선을 추출하지 않는다. boolean 조건 입력은 상위 adapter 검증에
의존한다. 프레임 투영·SLAM·모델 추론·Nav2 통신·실물 출력은 후속 구현이 필요하다.
