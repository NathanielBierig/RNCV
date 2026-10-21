"""Reframe: don't need two whole skeletons. Pool joints from ALL raw candidates (RTMO-m + v1, no select())
and assign RNC roles directly. Scored against roles_gt.csv (+ negative frames) by score_roles.py.

Per frame:
  1. candidates = every raw skeleton of both models, minus junk (two_fighters.implausible), referee-like
     (dark-aware referee_score > two_fighters.REF_THR) and crowd (box < 15% of the largest).
  2. head anchors = candidates with a head (any of nose/eyes/ears) + >= 1 shoulder at conf >= THR, head-to-
     shoulder distance consistent with the shoulder width. Duplicates (same head from 2 models) are clustered.
  3. arm evidence for an anchor = 'foreign' wrists/elbows (conf >= LOW, any candidate, merged ones too) within
     ARM_R shoulder-widths of the anchor's neck. Foreign = the joint's own shoulder (same candidate, same side)
     is not on one of the anchor's shoulders (a limb whose shoulder isn't visible is not counted).
  4. defender = the anchor cluster with the most arm evidence (tie: most confident head).
  5. facts: arm_across_neck (>= ARM_MIN foreign arm joints), arm_position (under_chin if the nearest foreign
     forearm joint sits at neck level, over_jaw if at/above the head centre), hooks (foreign knee/ankle within
     HOOK_R of the defender's hips; hips estimated from the torso when hidden), back_control (arm or hook evidence;
     BACK_RULE="two_heads" also needs another head within BACK_R of the defender's head).
Temporal smoothing: majority vote of each fact over the last SMOOTH_S seconds (cached at stride 2).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import tf  # noqa: E402
from referee import referee_score  # noqa: E402  (dark-aware since commit 2374308)

THR, LOW = 0.3, 0.2
HEAD = [0, 1, 2, 3, 4]
L_SH, R_SH, L_HIP, R_HIP = 5, 6, 11, 12
ARM = {7: 5, 9: 5, 8: 6, 10: 6}            # elbow/wrist -> its shoulder
LEG = {13: 11, 15: 11, 14: 12, 16: 12}     # knee/ankle -> its hip
ARM_R, ARM_MIN, HOOK_R, BACK_R = 1.0, 1, 1.5, 1.5
SMOOTH_S = 0.5
BACK_RULE = "evidence"      # "evidence": arm or hook evidence; "two_heads": also needs a 2nd head nearby


def candidates(cands, img):
    """cands: list of (kpts [17,2], scores [17]) -> filtered list."""
    out = [(k, s) for k, s in cands if not tf.implausible(k, s)]
    if img is not None:
        out = [(k, s) for k, s in out if referee_score(img, k, s) <= tf.REF_THR]
    if out:
        a = np.array([tf.box_area(k, s) for k, s in out])
        out = [c for c, ai in zip(out, a) if ai >= 0.15 * a.max()]
    return out


def anchor(k, s):
    """Head point, neck point, shoulder width, shoulders, confidence for one candidate; None if no head+shoulder."""
    h = [j for j in HEAD if s[j] >= THR]
    sh = [j for j in (L_SH, R_SH) if s[j] >= THR]
    if not h or not sh:
        return None
    head = k[h].mean(0)
    smid = k[sh].mean(0)
    if len(sh) == 2:
        sw = np.linalg.norm(k[L_SH] - k[R_SH])
        d = np.linalg.norm(head - smid)
        if not (0.2 * sw < d < 2.0 * sw):     # head not where a head sits relative to the shoulders
            return None
    else:
        sw = 2.0 * np.linalg.norm(head - smid)
    sw = max(sw, 10.0)
    neck = smid + 0.3 * (head - smid)
    return dict(head=head, neck=neck, smid=smid, sw=sw, sh={j: k[j] for j in sh},
                conf=float(s[h].max() + s[sh].sum()), k=k, s=s)


def cluster(anchors):
    """Merge anchors whose heads are within 0.5 shoulder-widths (same person seen by 2 models / duplicates)."""
    groups = []
    for a in sorted(anchors, key=lambda a: -a["conf"]):
        for g in groups:
            if np.linalg.norm(a["head"] - g[0]["head"]) < 0.5 * g[0]["sw"]:
                g.append(a)
                break
        else:
            groups.append([a])
    return groups


def owned(k, s, j, parent, group, sw):
    """True if limb joint j of candidate (k, s) hangs from a shoulder/hip that coincides with the group's."""
    if s[parent] < LOW:          # can't tell whose limb it is -> don't count it as the choker's
        return True
    for a in group:
        ref = a["k"][parent] if a["s"][parent] >= LOW else None
        others = [a["k"][q] for q in ((L_SH, R_SH) if parent in (L_SH, R_SH) else (L_HIP, R_HIP)) if a["s"][q] >= LOW]
        for p in ([ref] if ref is not None else []) + others:
            if np.linalg.norm(k[parent] - p) < 0.4 * sw:
                return True
    return False


def hips(a, group):
    pts = [g["k"][j] for g in group for j in (L_HIP, R_HIP) if g["s"][j] >= THR]
    if pts:
        return np.mean(pts, 0)
    return a["smid"] + 2.0 * a["sw"] * (a["smid"] - a["head"]) / (np.linalg.norm(a["smid"] - a["head"]) + 1e-6)


def evidence(group, cands):
    a = group[0]
    sw, neck, head = a["sw"], a["neck"], a["head"]
    arm, leg = [], []
    waist = hips(a, group)
    for k, s in cands:
        for j, p in ARM.items():
            if s[j] >= LOW and np.linalg.norm(k[j] - neck) < ARM_R * sw and not owned(k, s, j, p, group, sw):
                arm.append(k[j])
        for j, p in LEG.items():
            if s[j] >= LOW and np.linalg.norm(k[j] - waist) < HOOK_R * sw and not owned(k, s, j, p, group, sw):
                leg.append(k[j])
    return arm, leg, waist


def frame_roles(cands, img):
    """-> dict(neck, arm, arm_position, hooks, back, n_anchor) for one frame (neck None if no anchor)."""
    cands = candidates(cands, img)
    groups = cluster([a for a in (anchor(k, s) for k, s in cands) if a is not None])
    if not groups:
        return dict(neck=None, arm=False, arm_position="", hooks=False, back=False, n_anchor=0)
    scored = []
    for g in groups:
        arm, leg, waist = evidence(g, cands)
        scored.append((len(arm), g[0]["conf"], g, arm, leg))
    n_arm, _, g, arm, leg = max(scored, key=lambda x: (x[0], x[1]))
    a = g[0]
    pos = ""
    if len(arm) >= ARM_MIN:
        p = min(arm, key=lambda q: np.linalg.norm(q - a["neck"]))
        axis = a["smid"] - a["head"]
        t = float(np.dot(p - a["head"], axis) / (np.dot(axis, axis) + 1e-6))   # 0 = head centre, 1 = shoulders
        pos = "over_jaw" if t < 0.25 else "under_chin"
    other_head = any(np.linalg.norm(o[0]["head"] - a["head"]) < BACK_R * a["sw"] for o in groups if o is not g)
    has_arm, has_leg = len(arm) >= ARM_MIN, len(leg) >= 1
    back = (has_arm or has_leg) if BACK_RULE == "evidence" else bool(other_head and (has_arm or has_leg))
    return dict(neck=a["neck"], arm=has_arm, arm_position=pos, hooks=has_leg, back=back, n_anchor=len(groups))


def smooth(per_frame, fps_eff):
    """Majority vote of the boolean facts over the last SMOOTH_S s; neck/position from the last frame."""
    n = max(1, int(round(SMOOTH_S * fps_eff)))
    win = per_frame[-n:]
    out = dict(per_frame[-1])
    for f in ("arm", "hooks", "back"):
        out[f] = sum(r[f] for r in win) * 2 > len(win)
    if out["arm"] and not out["arm_position"]:
        pos = [r["arm_position"] for r in win if r["arm_position"]]
        out["arm_position"] = max(set(pos), key=pos.count) if pos else ""
    return out
