"""A/S03. 폐곡선 경로 길이·근방 투영 가이드.
완성된 중심선 추출기가 아니다. 입력 마지막 점은 첫 점을 반복하지 않는다.
벽/로봇 외곽 여유, 전체 선분 충돌 검사는 지도 adapter에서 별도 수행한다.
"""
import math

class LoopPath:
    def __init__(self, points):
        self.points = [tuple(p) for p in points]
        if len(points) < 3 or any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in points):
            raise ValueError('need >=3 finite XY points')
        self.lengths = [math.dist(p, self.points[(i+1)%len(points)]) for i,p in enumerate(points)]
        if min(self.lengths) <= 1e-6:
            raise ValueError('duplicate consecutive points')
        self.starts = []; total = 0.
        for length in self.lengths:
            self.starts.append(total); total += length
        self.length = total

    def project(self, xy, previous_segment=None, window=2, max_error=.5):
        if len(xy) != 2 or not all(math.isfinite(x) for x in xy) or max_error <= 0:
            raise ValueError('invalid pose')
        n = len(self.points)
        if previous_segment is not None and not 0 <= previous_segment < n:
            raise ValueError('invalid segment')
        indices = range(n) if previous_segment is None else sorted({(previous_segment+k)%n for k in range(-window,window+1)})
        candidates = []
        for i in indices:
            a,b = self.points[i], self.points[(i+1)%n]
            dx,dy = b[0]-a[0],b[1]-a[1]
            t = max(0.,min(1., ((xy[0]-a[0])*dx+(xy[1]-a[1])*dy)/self.lengths[i]**2))
            distance = math.dist(xy,(a[0]+t*dx,a[1]+t*dy))
            candidates.append((distance,i,t))
        error,i,t = min(candidates)
        if error > max_error:
            raise ValueError('pose outside path corridor')
        return {'segment': i, 's': (self.starts[i]+t*self.lengths[i])%self.length, 'error': error}

def demo():
    p = LoopPath([(0,0),(2,0),(2,1),(0,1)])
    return {'length': p.length, 'projection': p.project((.5,.1),0,1)}


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("navigation/path_manager", demo, args)


if __name__ == "__main__":
    main()
