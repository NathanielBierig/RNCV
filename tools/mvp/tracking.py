"""Fighter tracking layer for the MVP overlay: what the vision system sees, drawn on the fighters.

Only draws what is reliable (research/pose_review/REVIEW.md: whole skeletons are often mixed in tangled
positions, but person boxes and confident heads/limbs are usable):
  - corner-bracket box around the pair (union of the person boxes overlapping the top box), smoothed
  - a target reticle on each confidently seen head
  - limb segments only where both joints are confident (faded, so mixed skeletons don't dominate)
  - during an attempt, a "choke reticle" ON the fighters: a ring at the choke point (between the two heads)
    whose arc is the defender's choke meter, with the attacker's finish chance on a leader line
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
        self.spt = None                          # smoothed choke point
        self.ca, self.cb = color_a, color_b       # BGR: orange (attacker side), blue

    def choke_point(self, kp, box):
        """Where the choke happens: between the two closest confident heads, else one head, else the box top."""
        heads = []
        for p in kp:
            hv = [h for h in HEAD if p[h, 2] > HEAD_THR - 0.15]
            if hv:
                heads.append(p[hv, :2].mean(0))
        size = (np.ptp(box[[0, 2]]) + np.ptp(box[[1, 3]])) if box is not None else 400
        # in an RNC the two heads touch: only head pairs this close count (a referee's head is also in the pile)
        cands = [(a + b) / 2 for n, a in enumerate(heads) for b in heads[n + 1:] if np.linalg.norm(a - b) < 0.12 * size]
        if self.spt is not None:                # stay on the choke being tracked; hold still when unsure
            if not cands:
                return self.spt
            best = min(cands, key=lambda c: np.linalg.norm(c - self.spt))
            return best if np.linalg.norm(best - self.spt) < 0.15 * size else self.spt
        if cands:
            return cands[0]
        if len(heads) >= 2:
            d = [(np.linalg.norm(a - b), (a + b) / 2) for n, a in enumerate(heads) for b in heads[n + 1:]]
            return min(d, key=lambda x: x[0])[1]
        if heads:
            return heads[0]
        if box is not None:
            x0, y0, x1, y1 = box
            return np.array([(x0 + x1) / 2, y0 + 0.3 * (y1 - y0)])
        return None

    def reticle(self, img, t, fin, air, banner):
        if self.spt is None:
            return
        H = img.shape[0]
        sc = H / 720
        cx, cy = self.spt.astype(int)
        R = int(np.clip(0.07 * (np.ptp(self.sbox[[0, 2]]) + np.ptp(self.sbox[[1, 3]])) if self.sbox is not None else 40, 30 * sc, 70 * sc))
        a = 1.0 if air is None else float(np.clip(air, 0, 1))
        col = (113, 204, 46) if a > .6 else (60, 200, 255) if a > .3 else (70, 70, 235)     # BGR green / amber / red
        if a < .3:
            R += int(4 * sc * np.sin(t * 10))                                            # urgent pulse
        over = img.copy()
        cv2.circle(over, (cx, cy), R, tuple(int(0.35 * v) for v in col), int(7 * sc), cv2.LINE_AA)   # the drained part stays visible
        if a > 0.005:
            cv2.ellipse(over, (cx, cy), (R, R), -90, 0, 360 * a, col, int(6 * sc), cv2.LINE_AA)
        for k in range(4):                                                               # slow-turning ticks
            ang = t * 0.8 + k * np.pi / 2
            p0 = (int(cx + (R + 6 * sc) * np.cos(ang)), int(cy + (R + 6 * sc) * np.sin(ang)))
            p1 = (int(cx + (R + 16 * sc) * np.cos(ang)), int(cy + (R + 16 * sc) * np.sin(ang)))
            cv2.line(over, p0, p1, col, max(1, int(2 * sc)), cv2.LINE_AA)
        cv2.circle(over, (cx, cy), max(2, int(3 * sc)), col, -1, cv2.LINE_AA)
        # leader line to the readout (flipped to the left near the right edge)
        side = -1 if cx > img.shape[1] * 0.7 else 1
        ex, ey = int(cx + side * (R + 50 * sc)), int(cy - R - 40 * sc)
        sx, sy = int(cx + side * R * 0.7), int(cy - R * 0.7)
        cv2.line(over, (sx, sy), (ex, ey), self.ca, max(1, int(2 * sc)), cv2.LINE_AA)
        W_ = int(190 * sc)
        tx = ex if side > 0 else ex - W_
        # dark card behind the readout so it reads on a bright mat
        cv2.rectangle(over, (tx - int(6 * sc), ey - int(36 * sc)), (tx + W_, ey + int(30 * sc)), (20, 16, 14), -1)
        cv2.line(over, (tx - int(6 * sc), ey - int(36 * sc)), (tx - int(6 * sc), ey + int(30 * sc)), self.ca, max(2, int(3 * sc)))
        big = banner if banner else (f"FINISH {round(100 * fin):d}%" if fin is not None else "")
        cv2.putText(over, big, (tx + int(4 * sc), ey - int(8 * sc)), cv2.FONT_HERSHEY_DUPLEX, 0.95 * sc,
                    (70, 70, 235) if banner else self.ca, max(2, int(2 * sc)), cv2.LINE_AA)
        if air is not None and not banner:
            cv2.putText(over, f"CHOKE METER {round(100 * a):d}", (tx + int(4 * sc), ey + int(20 * sc)), cv2.FONT_HERSHEY_DUPLEX,
                        0.6 * sc, col, max(1, int(2 * sc)), cv2.LINE_AA)
        cv2.addWeighted(over, 0.9, img, 0.1, 0, dst=img)

    def draw(self, frame, i, t, live, fin=None, air=None, banner=None):
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
        for n, p in enumerate(kp if not (live or banner) else []):     # skeletons off during an attempt: reticle only
            c = self.ca if n == 0 else self.cb
            for a, bb in SKEL:
                if p[a, 2] > KP_THR and p[bb, 2] > KP_THR:
                    cv2.line(over, tuple(p[a, :2].astype(int)), tuple(p[bb, :2].astype(int)), c, 3, cv2.LINE_AA)
            for q in range(5, 17):
                if p[q, 2] > KP_THR:
                    cv2.circle(over, tuple(p[q, :2].astype(int)), 4, c, -1, cv2.LINE_AA)
            hv = [h for h in HEAD if p[h, 2] > HEAD_THR]
            if hv and not (live or banner):                     # during an attempt the choke reticle replaces these
                hx, hy = p[hv, :2].mean(0).astype(int)
                r = 16 + int(3 * np.sin(t * 6))                 # pulsing target reticle
                cv2.circle(img, (hx, hy), r, c, 2, cv2.LINE_AA)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv2.line(img, (hx + dx * (r - 6), hy + dy * (r - 6)), (hx + dx * (r + 8), hy + dy * (r + 8)), c, 2, cv2.LINE_AA)
        cv2.addWeighted(over, 0.55, img, 0.45, 0, dst=img)
        if live or banner:
            pt = self.choke_point(kp, self.sbox)
            if pt is not None:
                self.spt = pt if self.spt is None else 0.8 * self.spt + 0.2 * pt
            self.reticle(img, t, fin, air, banner)
        else:
            self.spt = None
        return img
