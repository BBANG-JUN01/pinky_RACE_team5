"""B/S06. YOLO 등 외부 모델 출력 정규화 가이드. 모델 로딩/추론은 미연결.
rows=[{label, confidence, xyxy:[x1,y1,x2,y2]}], 픽셀 단위.
빈 결과는 '사람 없음'의 충분조건이 아니다. frame freshness와 추론 상태를 함께 전달.
"""
import math

def normalize(rows, width, height, captured_at, threshold=.6):
    if width <= 0 or height <= 0 or not math.isfinite(captured_at) or not 0 <= threshold <= 1:
        raise ValueError('invalid frame metadata')
    result = []
    for row in rows:
        score = row['confidence']; box = row['xyxy']
        if len(box)!=4 or not all(math.isfinite(x) for x in [score,*box]): continue
        x1,y1,x2,y2=box
        if not threshold <= score <= 1 or not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height): continue
        result.append({'label':row['label'],'confidence':score,'xyxy':list(box),
                       'captured_at':captured_at,'range_valid':False})
    return result

def demo():
    return normalize([{'label':'person','confidence':.9,'xyxy':[10,10,30,50]}],640,480,1.)


def main(args=None):
    from pinky_gp_core.guide_cli import run
    run("perception/detector", demo, args)


if __name__ == "__main__":
    main()
