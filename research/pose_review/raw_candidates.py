"""Is the right skeleton ever proposed? Draw EVERY raw detection (own colour each, before select())
for a few hard eval frames and several detector settings:
  RTMO-m 0.3/0.65 | v1 0.25/0.65 | v1 0.25/0.9 (looser NMS) | v2 0.25/0.65
If no candidate sits on the choker, the fix must be in the detector, not in select()/the referee filter.
Also counts candidates per frame over all 48 eval frames.

    C:/Users/netan/.venvs/rncv/Scripts/python -I research/pose_review/raw_candidates.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, ROOT, SKEL, load_cache, tf  # noqa: E402
from yolo_pose_onnx import YoloPoseOnnx  # noqa: E402

HARD = [(4, "mid"), (7, "mid"), (5, "start"), (3, "mid"), (16, "end"), (14, "start")]
PAL = [(0, 165, 255), (255, 255, 0), (255, 0, 255), (0, 255, 0), (0, 0, 255), (255, 128, 0)]


def draw_all(img, K, S):
    im = img.copy()
    sc = max(2, img.shape[1] // 500)
    for i, (k, s) in enumerate(zip(K, S)):
        c = PAL[i % len(PAL)]
        for a, b in SKEL:
            if s[a] >= tf.THR and s[b] >= tf.THR:
                cv2.line(im, tuple(map(int, k[a])), tuple(map(int, k[b])), c, sc + 1, cv2.LINE_AA)
        if s[0] >= tf.THR:
            cv2.circle(im, tuple(map(int, k[0])), sc + 5, c, -1)
    return im


def main():
    v1 = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    v2 = YoloPoseOnnx(ROOT / "models/rncv_pose_v2.onnx")
    cache = load_cache()
    counts = {"rtmo": [], "v1_65": [], "v1_90": [], "v2_65": []}
    rows = []
    for e in cache:
        img = cv2.imread(str(OUT / "frames" / f"r{e['row']:02d}_{e['pos']}.jpg"))
        ka, sa = e["seq"][-1]["rtmo"]
        sets = {"rtmo": (ka, sa), "v1_65": v1(img, 0.65, 0.25), "v1_90": v1(img, 0.9, 0.25), "v2_65": v2(img, 0.65, 0.25)}
        for n, (k, s) in sets.items():
            counts[n].append(len(k))
        if (e["row"], e["pos"]) in HARD:
            pts = np.concatenate([k[s >= tf.THR] for k, s in zip(*sets["v1_90"])] or [np.array([[0, 0], img.shape[1::-1]])])
            x0, y0 = np.maximum(pts.min(0) - 60, 0).astype(int)
            x1, y1 = (pts.max(0) + 60).astype(int)
            pan = []
            for n, (k, s) in sets.items():
                c = draw_all(img, k, s)[y0:y1, x0:x1]
                c = cv2.resize(c, (int(c.shape[1] * 260 / c.shape[0]), 260))
                cv2.putText(c, f"r{e['row']} {e['pos']} {n} n={len(k)}", (4, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                pan.append(c)
            rows.append(np.hstack(pan))
    w = max(r.shape[1] for r in rows)
    rows = [cv2.copyMakeBorder(r, 0, 3, 0, w - r.shape[1], cv2.BORDER_CONSTANT) for r in rows]
    cv2.imwrite(str(OUT / "raw_candidates.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    for n, c in counts.items():
        c = np.array(c)
        print(f"{n}: candidates per frame median {np.median(c):.0f}, frames with >= 2: {(c >= 2).sum()}/48")


if __name__ == "__main__":
    main()
