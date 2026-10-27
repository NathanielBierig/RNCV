"""Save tight head/neck crops for every labeled attempt, so factor models can be trained after the videos are deleted.

    python -I tools/save_neck_crops.py           # all labeled clips still on disk that have no crops yet

For each attempt (start - 2 s to end + 1 s) at 4 frames per second: the fine-tuned pose model finds the fighters (the
referee is dropped, src/referee.py), and the crop is a square around their confident heads (the choke happens
there; research/attempt_clf/extract_neck.py). Saved as 224x224 JPEGs in data/crops/<clip>/<seconds>.jpg with an
index.csv (time, attempt row key). These are UFC pixels: LOCAL ONLY (data/ is git-ignored), never uploaded.
Run it before a labeled video is deleted (the cleanup only removes clips that have crops and features).
"""
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
FPS_OUT, PRE, POST, SIZE, REF_THR = 4.0, 2.0, 1.0, 224, 0.6
HEAD = [0, 1, 2, 3, 4]


def neck_square(k, s, b, keep):
    heads = [k[j][h] for j in keep for h in HEAD if s[j][h] > 0.3]
    if not heads:
        return None
    heads = np.array(heads)
    cx, cy = heads.mean(0)
    pile_h = b[keep, 3].max() - b[keep, 1].min()
    half = max(48.0, 0.35 * pile_h, 0.8 * (np.ptp(heads, axis=0).max() if len(heads) > 1 else 0))
    return cx, cy, half


def main():
    import attempt_clf as ac
    from referee import referee_score
    from yolo_pose_onnx import YoloPoseOnnx
    det = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    rows = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["video_url"], []).append(r)
    for name, rs in sorted(by.items()):
        path = ac.clip_path(name)
        out = ROOT / "data/crops" / name
        if not path.exists() or (out / "index.csv").exists():
            continue
        out.mkdir(parents=True, exist_ok=True)
        wins = [(float(r["video_time_start"]) - PRE, float(r["video_time_end"]) + POST,
                 "|".join([r["fight_id"], r["round"], r["video_url"], r["video_time_start"]])) for r in rs]
        cap = cv2.VideoCapture(str(path))
        idx, nxt, n = [], 0.0, 0
        for w0, w1, _ in sorted(wins):                   # jump to each attempt instead of playing the whole fight
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, w0 - 3.0) * 1000)
            while True:
                ok = cap.grab()
                t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                if not ok or t > w1:
                    break
                hit = [w for w in wins if w[0] <= t <= w[1]]
                if not hit or t < nxt:
                    continue
                nxt = t + 1 / FPS_OUT
                _, f = cap.retrieve()
                k, s = det(f, nms_thr=0.65, score_thr=0.25)
                b = det.last_boxes
                fighters = [j for j in range(len(b)) if referee_score(f, k[j], s[j]) <= REF_THR]
                if not fighters:
                    continue
                top = b[fighters[0]]
                keep = [j for j in fighters if not (b[j][2] < top[0] or b[j][0] > top[2] or b[j][3] < top[1] or b[j][1] > top[3])][:2]
                sq = neck_square(k, s, b, keep)
                if sq is None:
                    continue
                cx, cy, half = sq
                H, W = f.shape[:2]
                x0, y0, x1, y1 = int(max(0, cx - half)), int(max(0, cy - half)), int(min(W, cx + half)), int(min(H, cy + half))
                if x1 - x0 < 20 or y1 - y0 < 20:
                    continue
                fn = f"{t:08.2f}.jpg"
                cv2.imwrite(str(out / fn), cv2.resize(f[y0:y1, x0:x1], (SIZE, SIZE)), [cv2.IMWRITE_JPEG_QUALITY, 90])
                idx.append((fn, f"{t:.2f}", hit[0][2]))
                n += 1
        cap.release()
        with open(out / "index.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["file", "t", "row_key"])
            w.writerows(idx)
        print(f"{name}: {n} crops", flush=True)


if __name__ == "__main__":
    main()
