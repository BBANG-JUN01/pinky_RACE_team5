# pinky_gp_display 코드 안내

현재는 오프라인 가이드 구현. 실물 연결은 [ROS 연결 절차](../../docs/08_ROS_ADAPTER_GUIDE.md)를 따른다.

## display.display_manager

D/S08-S10. 최종 적용 상태 -> LED 의미와 LCD 텍스트. 드라이버는 미연결.
2~5Hz timer에서 frame 생성, 이전 frame과 다를 때만 비동기 출력한다.
LCD 오류는 별도 관제 오류이며 이 모듈은 모터 명령을 만들지 않는다.

핵심 API: `format_time, frame`

```bash
python3 scripts/run_module.py display.display_manager --demo
```

