"""Fighter tracking layer for the MVP overlay: what the vision system sees, drawn on the fighters.

Only draws what is reliable (research/pose_review/REVIEW.md: whole skeletons are often mixed in tangled
positions, but person boxes and confident heads/limbs are usable):
  - the referee is dropped first (src/referee.py: black shirt / trousers vs bare skin, threshold 0.6)
  - corner-bracket box around the pair (union of the person boxes overlapping the top box), smoothed
  - stick figures only as short flashes of steady, plausible poses (no gliding; the raw per-frame pose
    stays in the cache for the models)
  - during an attempt, a choke reticle ON the fighters whose arc is the defender's HP, shown only while two
    heads are confidently together (else hidden rather than drawn in the wrong spot). The numbers live in
    the on-video HUD (tools/mvp/hud.py), not here.
Pose = fine-tuned YOLO11m-pose ONNX (models/rncv_pose_v1.onnx) at a frame stride, cached to
data/mvp/<clip>_track2.npz.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SKEL = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
HEAD = [0, 1, 2, 3, 4]
KP_THR, HEAD_THR = 0.55, 0.45
REF_THR = 0.6                 # referee_score above this = referee (research/referee/, dark-aware rule)


def compute(clip, stride=2):
    cache = ROOT / "data/mvp" / f"{Path(clip).stem}_track2.npz"
    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        return d["boxes"], d["kpts"], int(d["stride"])
    sys.path.insert(0, str(ROOT / "src"))
    from referee import referee_score
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
            fighters = [j for j in range(len(b)) if referee_score(f, k[j], s[j]) <= REF_THR]
            pair, kp = None, np.zeros((0, 17, 3), np.float32)
            if fighters:
                top = b[fighters[0]]
                keep = [j for j in fighters if not (b[j][2] < top[0] or b[j][0] > top[2] or b[j][3] < top[1] or b[j][1] > top[3])][:2]
                pair = np.r_[b[keep, 0].min(), b[keep, 1].min(), b[keep, 2].max(), b[keep, 3].max()]
                kp = np.concatenate([k[keep], s[keep][..., None]], -1)
            boxes.append(pair if pair is not None else np.full(4, np.nan))
            kpts.append(kp)
        i += 1
    cap.release()
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, boxes=np.array(boxes), kpts=np.array(kpts, dtype=object), stride=stride)
    return np.array(boxes), np.array(kpts, dtype=object), stride


def hp_color(a):
    """BGR, blue (healthy) to red (drained): no green, it reads as 'good' (fresh-eyes review)."""
    f = float(np.clip((a - 0.2) / 0.6, 0, 1))
    blue, red = np.array([255, 194, 76]), np.array([60, 70, 255])
    return tuple(int(v) for v in red + (blue - red) * f)


LR_PAIRS = [((5, 7), (6, 8)), ((7, 9), (8, 10)), ((11, 13), (12, 14)), ((13, 15), (14, 16))]
STEADY = 0.15        # max joint movement between samples (torso lengths): about the steadiest 5% of poses
FLASH_HOLD, FLASH_GAP = 1.5, 6.0


def torso(p):
    return np.linalg.norm(p[[5, 6], :2].mean(0) - p[[11, 12], :2].mean(0)) + 1e-6


def plausible(p):
    """Left and right limbs about the same length (mixed-up skeletons usually fail this)."""
    for (a, b), (c, d) in LR_PAIRS:
        r = np.linalg.norm(p[a, :2] - p[b, :2]) / (np.linalg.norm(p[c, :2] - p[d, :2]) + 1e-6)
        if not 0.6 < r < 1.6:
            return False
    return True


class Layer:
    """Draws the tracking layer on a frame (in original video pixels). Owner feedback 2026-10-27: no gliding
    skeletons; flash a skeleton only when the pose is steady and plausible, hold it still, then let it go;
    the choke reticle locks on once and stays put (relative to the fighters' box) until the attempt ends."""

    def __init__(self, boxes, kpts, stride, color_a=(61, 138, 255), color_b=(255, 194, 76)):
        self.boxes, self.kpts, self.stride = boxes, kpts, stride
        self.sbox = None
        self.flash, self.next_flash = None, -1e9  # (poses, until), earliest next flash
        self.lock = None                          # reticle position as a fraction of the box
        self.ca, self.cb = color_a, color_b

    def steady(self, j):
        """Poses in sample j that barely moved over the previous two samples and look anatomically sane."""
        out = []
        for p in self.kpts[j]:
            if (p[5:17, 2] > KP_THR).sum() < 10 or not plausible(p):
                continue
            ok = True
            for back in (1, 2):
                prev = self.kpts[j - back] if j - back >= 0 else []
                if not len(prev):
                    ok = False; break
                c = p[5:17, :2].mean(0)
                q = min(prev, key=lambda q: np.linalg.norm(q[5:17, :2].mean(0) - c))
                if np.abs(p[5:17, :2] - q[5:17, :2]).sum(1).mean() / torso(p) > STEADY:
                    ok = False; break
            if ok:
                out.append(p.copy())
        return out

    def draw_poses(self, img, poses, alpha):
        over = img.copy()
        for n, p in enumerate(poses):
            c = self.ca if n == 0 else self.cb
            xy, ok = p[:, :2].astype(int), p[:, 2] > KP_THR
            for a, b in SKEL:
                if ok[a] and ok[b]:
                    cv2.line(over, tuple(xy[a]), tuple(xy[b]), c, 3, cv2.LINE_AA)
            for q in range(5, 17):
                if ok[q]:
                    cv2.circle(over, tuple(xy[q]), 5, c, -1, cv2.LINE_AA)
        cv2.addWeighted(over, alpha, img, 1 - alpha, 0, dst=img)

    def head_pair(self, kp, box):
        """The choke point = between two confident heads that touch (in an RNC they do); None if not sure."""
        heads = [p[[h for h in HEAD if p[h, 2] > HEAD_THR], :2].mean(0) for p in kp if (p[HEAD, 2] > HEAD_THR).any()]
        if len(heads) < 2 or box is None:
            return None
        size = np.ptp(box[[0, 2]]) + np.ptp(box[[1, 3]])
        dd, mid = min(((np.linalg.norm(a - b), (a + b) / 2) for n, a in enumerate(heads) for b in heads[n + 1:]),
                      key=lambda x: x[0])
        return mid if dd < 0.14 * size else None

    def ring(self, img, t, a, sc, cx, cy):
        R = int(np.clip(0.06 * (np.ptp(self.sbox[[0, 2]]) + np.ptp(self.sbox[[1, 3]])), 26 * sc, 60 * sc))
        col = hp_color(a)
        cv2.circle(img, (cx, cy), R, tuple(int(0.35 * v) for v in col), int(6 * sc), cv2.LINE_AA)
        if a > 0.005:
            cv2.ellipse(img, (cx, cy), (R, R), -90, 0, 360 * a, col, int(5 * sc), cv2.LINE_AA)
        for k in range(4):                                                               # slow-turning ticks
            ang = t * 0.8 + k * np.pi / 2
            p0 = (int(cx + (R + 6 * sc) * np.cos(ang)), int(cy + (R + 6 * sc) * np.sin(ang)))
            p1 = (int(cx + (R + 15 * sc) * np.cos(ang)), int(cy + (R + 15 * sc) * np.sin(ang)))
            cv2.line(img, p0, p1, col, max(1, int(2 * sc)), cv2.LINE_AA)

    def draw(self, frame, i, t, live, air=None, ended=False, fade=1.0):
        j = min(len(self.boxes) - 1, i // self.stride)
        b, kp = self.boxes[j], self.kpts[j]
        img = frame
        sc = img.shape[0] / 720
        if not np.isnan(b).any():
            self.sbox = b if self.sbox is None else 0.9 * self.sbox + 0.1 * b
        if self.sbox is not None and not ended:          # quiet corner brackets
            x0, y0, x1, y1 = self.sbox.astype(int)
            col = self.ca if live else (170, 170, 170)
            L = max(12, int(0.10 * min(x1 - x0, y1 - y0)))
            for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                cv2.line(img, (px, py), (px + dx * L, py), col, 2, cv2.LINE_AA)
                cv2.line(img, (px, py), (px, py + dy * L), col, 2, cv2.LINE_AA)
        if not ended and t >= self.next_flash:            # skeleton flash: steady poses only, held still
            good = self.steady(j)
            if good:
                self.flash, self.next_flash = (good, t + FLASH_HOLD), t + FLASH_GAP
        if self.flash and t < self.flash[1]:
            self.draw_poses(img, self.flash[0], 0.75 * min(1.0, (self.flash[1] - t) / 0.4))
        if live and not ended and self.sbox is not None:  # choke reticle: lock once, then stay put
            bx, by = self.sbox[0], self.sbox[1]
            bw, bh = max(1.0, self.sbox[2] - bx), max(1.0, self.sbox[3] - by)
            if self.lock is None:
                pt = self.head_pair(kp, self.sbox)
                if pt is not None:
                    self.lock = ((pt[0] - bx) / bw, (pt[1] - by) / bh)
            if self.lock is not None:
                over = img.copy()
                self.ring(over, t, 1.0 if air is None else float(np.clip(air, 0, 1)), sc,
                          int(bx + self.lock[0] * bw), int(by + self.lock[1] * bh))
                cv2.addWeighted(over, 0.9 * fade, img, 1 - 0.9 * fade, 0, dst=img)
        elif not live:
            self.lock = None
        return img
