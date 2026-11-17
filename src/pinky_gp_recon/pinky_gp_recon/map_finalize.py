"""A/S03. 지도+검증된 경로 파일의 버전 manifest 작성 가이드.
SLAM loop closure 이후 경로 재구성과 footprint 충돌 검사는 미구현이다.
이 함수는 외부 검사 완료 여부를 입력받으며 검사 성공을 스스로 증명하지 않는다.
"""
from pathlib import Path
import hashlib

def manifest(map_yaml, map_image, path_file, geometry_checked=False):
    if not geometry_checked:
        raise ValueError('map/path/footprint verification required')
    paths = [Path(p) for p in (map_yaml,map_image,path_file)]
    if any(not p.is_file() or p.stat().st_size == 0 for p in paths):
        raise ValueError('missing or empty artifact')
    return {'schema_version': 1, 'files': [
        {'name': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
        'geometry_check': 'caller_asserted; attach evidence', 'robot_b_loaded': False}

def demo():
    return {'workflow': ['SLAM finalize', 'reconstruct path', 'check footprint on every segment',
                         'manifest(map_yaml, map_image, path_file, geometry_checked=True)',
                         'transfer all files', 'verify hashes and localization on B']}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("recon/map_finalize", demo, args)


if __name__ == "__main__":
    main()
