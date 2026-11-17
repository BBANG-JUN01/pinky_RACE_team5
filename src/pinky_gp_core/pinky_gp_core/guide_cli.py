"""공통 오프라인 예제 실행기. ROS 토픽과 모터에 연결하지 않는다."""
import argparse
import json

def run(title, demo, args=None):
    parser = argparse.ArgumentParser(description=title)
    parser.add_argument('--demo', action='store_true', help='합성 입력 예제 실행')
    options = parser.parse_args(args)
    if not options.demo:
        parser.print_help()
        return
    print(json.dumps({'mode': 'OFFLINE_GUIDE', 'module': title,
                      'result': demo()}, ensure_ascii=False, indent=2, allow_nan=False))
