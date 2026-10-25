"""CLIP features on a head/neck crop (where the choke happens) instead of the whole fighter pair.

    python -I research/attempt_clf/extract_neck.py

Same frames and order as attempt_clf.py (so detector_v2.py can stack them with the other caches). Crop: the
fine-tuned pose model finds the pile (person boxes overlapping the top box, as in pair_crop); the crop is a square
around the mean of their confident head keypoints, sized from the pile and the spread of the heads. Falls back
to the pair crop when no head is confident. Output: data/attempt_clf/feats_neck.npz.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import attempt_clf as ac

HEAD, HEAD_THR = [0, 1, 2, 3, 4], 0.3
PAIR_CROP = ac.pair_crop          # original, kept for the fallback


def neck_crop(det, frame, pad=0.25):
    k, s = det(frame, nms_thr=0.65, score_thr=0.25)
    b = det.last_boxes
    if not len(b):
        return frame
    top = b[0]
    keep = [j for j, x in enumerate(b) if not (x[2] < top[0] or x[0] > top[2] or x[3] < top[1] or x[1] > top[3])][:3]
    heads = [k[j][h] for j in keep for h in HEAD if s[j][h] > HEAD_THR]
    if not heads:
        return PAIR_CROP(det, frame, pad)
    heads = np.array(heads)
    cx, cy = heads.mean(0)
    pile_h = b[keep, 3].max() - b[keep, 1].min()
    spread = np.ptp(heads, axis=0).max() if len(heads) > 1 else 0.0
    half = max(48.0, 0.35 * pile_h, 0.8 * spread)
    H, W = frame.shape[:2]
    x0, y0 = int(max(0, cx - half)), int(max(0, cy - half))
    x1, y1 = int(min(W, cx + half)), int(min(H, cy + half))
    return frame[y0:y1, x0:x1] if x1 > x0 + 10 and y1 > y0 + 10 else frame


if __name__ == "__main__":
    ac.CROP = True
    ac.CACHE = ac.ROOT / "data/attempt_clf/feats_neck.npz"
    ac.pair_crop = neck_crop          # extract() calls pair_crop(det, frame) for every sampled frame
    ac.extract(ac.clips_and_windows())
