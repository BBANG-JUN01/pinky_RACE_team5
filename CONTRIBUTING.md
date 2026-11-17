# 개발 규칙

- Python 3.10 이상. 패키지 간 의존성을 package.xml에 선언한다.
- 함수의 단위(m, rad, s), 좌표계, clock 출처를 docstring에 적는다.
- 센서 오류/timeout/미구현을 성공이나 준비 완료로 반환하지 않는다.
- 실측값과 예제값을 구분하고 유효하지 않은 float/NaN 입력을 거부한다.
- 테스트: `python3 scripts/check_core.py`, `python3 scripts/guide_smoke.py`.
- 주행 변경은 재생·현장 증거를 PR에 첨부한다. 현장 미검증이면 명시한다.
- bag, 모델 가중치, 개인 토큰, 실제 네트워크 비밀번호는 커밋하지 않는다.
- 진행 상태는 `scripts/progress.py`로 변경하고 `scripts/export_progress.py`로 표를 갱신한다.
- 제조사 코드를 복제·변경하기보다 adapter로 연결하고 버전과 라이선스를 기록한다.

브랜치/리뷰/노션 운영은 [팀 운영](docs/09_TEAM_WORKFLOW.md)을 따른다.
