# pinky_gp_dashboard 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

## dashboard.operator_server

D/S05-S08. 관제 명령 생성 계약. HTTP 서버/인증/ROS 서비스는 미연결.
운영 UI는 여기서 생성한 command_id를 재전송에도 유지한다.
accepted와 실제 완료를 구분해서 표시하고 모든 요청/결과를 JSONL로 기록한다.

핵심 API: `OperatorCommand`

```bash
python3 scripts/run_module.py dashboard.operator_server --demo
```

