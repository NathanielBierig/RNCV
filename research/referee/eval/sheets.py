"""Labeling sheets: one image per eval frame (data/referee/label_sheets/).

Top: the frame with each person's skeleton + box and index. People whose box is
< 15% of the largest (what select() calls crowd) get a thin grey box.
Bottom: crops of the non-crowd people with their skeleton, for judging clothes.
    python -I research/referee/eval/sheets.py
"""
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402

OUT = ROOT / "data" / "referee"
SKELETON = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
COLORS = [(0, 0, 255), (0, 200, 0), (255, 80, 0), (0, 200, 255), (255, 0, 255), (255, 255, 0),
          (0, 128, 255), (160, 0, 255), (255, 160, 0), (128, 255, 128), (80, 80, 255), (0, 255, 160)]


def load_dets():
    d = {}
    for f in (OUT / "dets").glob("*.npz"):
        z = np.load(f, allow_pickle=True)
        d[f.stem] = {int(i): (k, s) for i, k, s in zip(z["frame_idx"], z["kpts"], z["scores"])}
    return d


def skel(img, k, s, c, t=3):
    for a, b in SKELETON:
        if s[a] >= tf.THR and s[b] >= tf.THR:
            cv2.line(img, tuple(map(int, k[a])), tuple(map(int, k[b])), c, t)
    for j in np.where(s >= tf.THR)[0]:
        cv2.circle(img, tuple(map(int, k[j])), t + 2, c, -1)


def main():
    dets = load_dets()
    rows = list(csv.DictReader(open(OUT / "candidates.csv")))
    frames = sorted({(r["clip"], int(r["frame"])) for r in rows})
    (OUT / "label_sheets").mkdir(exist_ok=True)
    for clip, f in frames:
        img = cv2.imread(str(OUT / "frames" / f"{clip}_{f}.jpg"))
        K, S = dets[clip][f]
        areas = np.array([tf.box_area(k, s) for k, s in zip(K, S)])
        crowd = areas < 0.15 * max(areas.max(), 1)
        vis = img.copy()
        crops = []
        for j, (k, s) in enumerate(zip(K, S)):
            r = next(r for r in rows if r["clip"] == clip and int(r["frame"]) == f and int(r["person_idx"]) == j)
            x0, y0, x1, y1 = (int(r[c]) for c in ("x0", "y0", "x1", "y1"))
            c = COLORS[j % len(COLORS)]
            if crowd[j]:
                cv2.rectangle(vis, (x0, y0), (x1, y1), (160, 160, 160), 2)
                cv2.putText(vis, str(j), (x0 + 3, y0 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
                continue
            skel(vis, k, s, c)
            cv2.rectangle(vis, (x0, y0), (x1, y1), c, 2)
            cv2.putText(vis, str(j), (x0 + 6, y0 + 50), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 10)
            cv2.putText(vis, str(j), (x0 + 6, y0 + 50), cv2.FONT_HERSHEY_SIMPLEX, 2.0, c, 4)
            cr = img[max(0, y0):y1, max(0, x0):x1].copy()
            kk = k - [max(0, x0), max(0, y0)]
            skel(cr, kk, s, c, 2)
            h = 300
            cr = cv2.resize(cr, (max(1, int(cr.shape[1] * h / cr.shape[0])), h))
            cv2.putText(cr, str(j), (5, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 8)
            cv2.putText(cr, str(j), (5, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.6, c, 3)
            crops.append(cr)
        top = cv2.resize(vis, (1280, 720))
        cv2.putText(top, f"{clip} {f}", (15, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        strip = np.zeros((300, 1280, 3), np.uint8)
        x = 0
        for cr in crops:
            w = min(cr.shape[1], 1280 - x)
            if w <= 0:
                break
            strip[:, x:x + w] = cr[:, :w]
            x += w + 6
        cv2.imwrite(str(OUT / "label_sheets" / f"{clip}_{f:05d}.jpg"), np.vstack([top, strip]))


if __name__ == "__main__":
    main()
