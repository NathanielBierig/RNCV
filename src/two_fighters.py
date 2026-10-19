"""Pick and track the two fighters among low-threshold RTMO detections.

Ported from research/pose_sweep/select2.py (see FINDINGS.md there). RTMO at
score_thr 0.3 finds the tangled second fighter far more often than the default
0.7, but also returns the referee, crowd and duplicate skeletons. Per frame:
  1. crowd: drop people whose box is < 15% of the largest box's area
  2. duplicates: drop a person whose confident joints mostly coincide with a
     better-scored person's (same body detected twice)
  3. referee by appearance (when the frame is given): drop people whose
     torso/arms/legs show little skin (src/referee.py; fighters are shirtless,
     the referee is in black). On the 128-frame eval set this cut "referee
     kept" from 58% to 10% with 1 fighter wrongly flagged
     (research/referee/appearance/RESULTS.md). It may leave only one person.
  4. with 3+ candidates left, keep the most-overlapping pair (fighters in a
     choke overlap; the referee stands apart).
Then a 2-slot tracker (Hungarian on joint positions) keeps identities and fills
a missing fighter from its last pose for up to 0.5 s, flagged as "filled".
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

from referee import referee_score

THR = 0.3
UPPER = [0, 5, 6, 7, 8, 9, 10]          # nose, shoulders, elbows, wrists
MISSING, SEEN, FILLED = 0, 1, 2


def box_area(k, s):
    p = k[s >= THR]
    if len(p) < 3:
        return 0.0
    w, h = p.max(0) - p.min(0)
    return float(w * h)


def _same_body(k1, s1, k2, s2, scale):
    both = (s1 >= THR) & (s2 >= THR)
    if both.sum() < 5:
        return False
    return np.median(np.linalg.norm(k1[both] - k2[both], axis=1)) < 0.08 * scale


def _box(k, s):
    p = k[s >= THR] if (s >= THR).sum() >= 3 else k
    return np.r_[p.min(0), p.max(0)]


def _iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w * h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


REF_THR = 0.5


def select(kpts, scores, img=None):
    """kpts [N,17,2], scores [N,17], img = BGR frame (optional, enables the
    appearance referee filter) -> (kept kpts, kept scores, dropped kpts, counts)."""
    counts = {"crowd": 0, "dup": 0, "ref_look": 0, "ref": 0}
    if not len(scores):
        return kpts, scores, [], counts
    order = np.argsort(-scores.mean(1))
    kpts, scores = kpts[order], scores[order]
    areas = np.array([box_area(k, s) for k, s in zip(kpts, scores)])
    keep, dropped = [], []
    for i, (k, s) in enumerate(zip(kpts, scores)):
        if areas.max() > 0 and areas[i] < 0.15 * areas.max():
            counts["crowd"] += 1; dropped.append(i); continue
        scale = np.sqrt(max(areas[i], 1.0))
        if any(_same_body(k, s, kpts[j], scores[j], scale) for j in keep):
            counts["dup"] += 1; dropped.append(i); continue
        keep.append(i)
    if img is not None:
        looks_ref = [i for i in keep if referee_score(img, kpts[i], scores[i]) > REF_THR]
        counts["ref_look"] += len(looks_ref); dropped += looks_ref
        keep = [i for i in keep if i not in looks_ref]
    if len(keep) > 2:
        boxes = {i: _box(kpts[i], scores[i]) for i in keep}
        best = max(((a, b) for x, a in enumerate(keep) for b in keep[x + 1:]),
                   key=lambda ab: (_iou(boxes[ab[0]], boxes[ab[1]]), -ab[0] - ab[1]))
        others = [i for i in keep if i not in best]
        counts["ref"] += len(others); dropped += others
        keep = list(best)
    return kpts[keep], scores[keep], [kpts[i] for i in dropped], counts


class TwoSlotTracker:
    """Online 2-identity tracker; fills a missing fighter for up to max_gap_s."""

    def __init__(self, fps_eff, max_gap_s=0.5):
        self.fps_eff, self.max_gap_s = fps_eff, max_gap_s
        self.slots, self.last_seen, self.t = [None, None], [-1e9, -1e9], -1

    def update(self, ks, ss):
        """Returns (poses [2,17,3] with NaN for missing, states [2])."""
        self.t += 1
        assigned = [None, None]
        if len(ks):
            cost = np.full((len(ks), 2), 1e6)
            for i, (k, s) in enumerate(zip(ks, ss)):
                for j in range(2):
                    if self.slots[j] is None:
                        cost[i, j] = 1e5
                        continue
                    pk, ps = self.slots[j]
                    m = (s >= THR) & (ps >= THR)
                    if m.any():
                        cost[i, j] = np.linalg.norm(k[m] - pk[m], axis=1).mean()
            for i, j in zip(*linear_sum_assignment(cost)):
                assigned[j] = (ks[i], ss[i])
                self.slots[j] = (ks[i], ss[i])
                self.last_seen[j] = self.t
        poses = np.full((2, 17, 3), np.nan, dtype=np.float32)
        states = np.zeros(2, dtype=np.int8)
        for j in range(2):
            if assigned[j] is not None:
                states[j] = SEEN
            elif self.slots[j] is not None and (self.t - self.last_seen[j]) / self.fps_eff <= self.max_gap_s:
                states[j] = FILLED
            else:
                continue
            k, s = self.slots[j]
            poses[j, :, :2], poses[j, :, 2] = k, s
        return poses, states


def upper_ok(s):
    return (s[UPPER] >= THR).sum() >= 5
