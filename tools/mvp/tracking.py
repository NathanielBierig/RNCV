"""Fighter tracking layer for the MVP overlay: what the vision system sees, drawn on the fighters.

Only draws what is reliable (research/pose_review/REVIEW.md: whole skeletons are often mixed in tangled
positions, but person boxes and confident heads/limbs are usable):
  - corner-bracket box around the pair (union of the person boxes overlapping the top box), smoothed
  - a target reticle on each confidently seen head
  - limb segments only where both joints are confident (faded, so mixed skeletons don't dominate)
Pose = fine-tuned YOLO11m-pose ONNX (models/rncv_pose_v1.onnx) at a frame stride, held between frames,
cached to data/mvp/<clip>_track.npz.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SKEL = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
HEAD = [0, 1, 2, 3, 4]
KP_THR, HEAD_THR = 0.55, 0.6


def compute(clip, stride=2):
    cache = ROOT / "data/mvp" / f"{Path(clip).stem}_track.npz"
    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        return d["boxes"], d["kpts"], int(d["stride"])
    sys.path.insert(0, str(ROOT / "src"))
    from yolo_pose_onnx import YoloPoseOnnx
    det = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    cap = cv2.VideoCapture(str(clip))
    boxes, kpts, i = [], [], 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i % stride == 0:
            k, s = det(f, nms_thr=0.65, score_thr=0.25)
            b = det.last_boxes
            pair = None
            if len(b):
                top = b[0]
                keep = [j for j, x in enumerate(b) if not (x[2] < top[0] or x[0] > top[2] or x[3] < top[1] or x[1] > top[3])][:3]
                pair = np.r_[b[keep, 0].min(), b[keep, 1].min(), b[keep, 2].max(), b[keep, 3].max()]
                kp = np.concatenate([k[keep], s[keep][..., None]], -1)
            else:
                kp = np.zeros((0, 17, 3), np.float32)
            boxes.append(pair if pair is not None else np.full(4, np.nan))
            kpts.append(kp)
        i += 1
    cap.release()
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, boxes=np.array(boxes), kpts=np.array(kpts, dtype=object), stride=stride)
    return np.array(boxes), np.array(kpts, dtype=object), stride


class Layer:
    """Draws the tracking layer on a frame (in original video pixels), with smoothing across frames."""

    def __init__(self, boxes, kpts, stride, color_a=(61, 138, 255), color_b=(255, 194, 76)):
        self.boxes, self.kpts, self.stride = boxes, kpts, stride
        self.sbox = None
        self.ca, self.cb = color_a, color_b       # BGR: orange (attacker side), blue

    def draw(self, frame, i, t, live):
        j = min(len(self.boxes) - 1, i // self.stride)
        b, kp = self.boxes[j], self.kpts[j]
        img = frame
        if not np.isnan(b).any():
            self.sbox = b if self.sbox is None else 0.75 * self.sbox + 0.25 * b
        if self.sbox is not None:
            x0, y0, x1, y1 = self.sbox.astype(int)
            col = self.ca if live else (180, 180, 180)
            L = max(12, int(0.12 * min(x1 - x0, y1 - y0)))
            for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                cv2.line(img, (px, py), (px + dx * L, py), col, 3, cv2.LINE_AA)
                cv2.line(img, (px, py), (px, py + dy * L), col, 3, cv2.LINE_AA)
            tag = "RNC ATTEMPT" if live else "TRACKING"
            cv2.putText(img, tag, (x0, max(18, y0 - 10)), cv2.FONT_HERSHEY_DUPLEX, 0.7, col, 2, cv2.LINE_AA)
        over = img.copy()
        for n, p in enumerate(kp):
            c = self.ca if n == 0 else self.cb
            for a, bb in SKEL:
                if p[a, 2] > KP_THR and p[bb, 2] > KP_THR:
                    cv2.line(over, tuple(p[a, :2].astype(int)), tuple(p[bb, :2].astype(int)), c, 3, cv2.LINE_AA)
            for q in range(5, 17):
                if p[q, 2] > KP_THR:
                    cv2.circle(over, tuple(p[q, :2].astype(int)), 4, c, -1, cv2.LINE_AA)
            hv = [h for h in HEAD if p[h, 2] > HEAD_THR]
            if hv:
                hx, hy = p[hv, :2].mean(0).astype(int)
                r = 16 + int(3 * np.sin(t * 6))                 # pulsing target reticle
                cv2.circle(img, (hx, hy), r, c, 2, cv2.LINE_AA)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv2.line(img, (hx + dx * (r - 6), hy + dy * (r - 6)), (hx + dx * (r + 8), hy + dy * (r + 8)), c, 2, cv2.LINE_AA)
        cv2.addWeighted(over, 0.55, img, 0.45, 0, dst=img)
        return img
