# 시험과 기록 규칙

## 먼저 시험할 오류

- RED 뒤 GREEN: ABORTED 유지.
- PERSON과 PENALTY 중 페널티 종료: PERSON 유지.
- 정상 명령이 끊김: 새 메시지 없이도 로컬 timer가 정지.
- DRS 중 YELLOW/SC/사람: 초록 LED 해제와 추가 출력 취소.
- 출발등 영상 가림: 오출발 없음.
- 체크포인트 건너뜀 또는 역방향 통과: 랩 미증가.
- 정찰 루프 폐쇄: 경로 끝과 시작의 불연속 검사.
- 지도 버전이 다른 B: GRID_READY 금지.
- 헤어핀 반대편 차: 앞차 또는 DRS 대상으로 미판정.
- 추월 중 장애물: 강제 복귀 대신 유효 경로 또는 정지 선택.

## 증거 템플릿

evidence/RESULT_TEMPLATE.md를 복사한다. bag·모델·대용량 원시 영상은 이 시작 패키지에
포함하지 않는다. 팀 저장소 또는 보관 위치의 식별자와 checksum을 결과에 기록한다.
단위 테스트 결과는 core의 규칙 근거일 뿐 S01 정지 기능의 실물 검증을 대체하지 않는다.

## 이벤트 로그 필드

race_id, robot_id, map_id, path_id, event_id, command_id, capture_stamp,
receive_stamp, monotonic_elapsed, source, phase, restriction, behavior,
stop_reasons, measured_speed, speed_cap, cap_reason, drs_eligible,
drs_active, lap, s_m, pose_valid, data_age, code_commit, config_hash.

## 시험 수치

절대 속도·timeout·DRS 간격·사람 보호 거리는 초기 미확정이다.
속도 단계별 정지 거리와 반응 지연을 측정한 뒤 설정한다.
기획서의 연속 완주·깃발·페널티·랜덤 물체 반복 시험에 각각 증거를 남긴다.
