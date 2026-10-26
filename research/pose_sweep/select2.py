"""Pick the two fighters out of low-threshold RTMO detections, automatically.

RTMO at score_thr 0.3 finds the second fighter far more often (see FINDINGS.md)
but also returns the referee, crowd members and duplicate skeletons. Per frame:
  1. crowd: drop people whose box is < 15% of the largest box's area
  2. duplicates: drop a person whose confident joints mostly coincide with a
     better-scored person's (same body detected twice)
  3. referee: with 3+ candidates keep the most-overlapping pair (fighters in a
     choke overlap; the referee stands apart). A black-shirt colour rule was
     tried and rejected: it dropped fighters in shadow (FINDINGS.md).
  4. keep the 2 best remaining, then a 2-slot tracker (Hungarian on joint
     positions) keeps identities; a missing fighter is filled from its last
     pose for up to 0.5 s ("fill in the blanks"), flagged as imputed.
No labels needed. Writes research/pose_sweep/select2.json + sample frames to
data/pose/select2/ (local only).

    python -I research/pose_sweep/select2.py --every 5
"""
import argparse
import glob
import json
from pathlib import Path

import cv2
import numpy as np
from rtmlib import RTMO
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[2]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
UPPER = [0, 5, 6, 7, 8, 9, 10]
THR = 0.3


def torso_darkness(img, k, s):
    """Mean brightness (HSV V, 0-255) inside the shoulder-hip quad; None if not visible."""
    idx = [5, 6, 12, 11]
    if (s[idx] < THR).any():
        return None
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, k[idx].astype(np.int32), 1)
    if mask.sum() < 50:
        return None
    v = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 2]
    return float(v[mask > 0].mean())


def forearm_brightness(img, k, s):
    """Mean V along both elbow->wrist segments; None if not visible."""
    v = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 2]
    vals = []
    for e, w in ((7, 9), (8, 10)):
        if s[e] >= THR and s[w] >= THR:
            for a in np.linspace(0.3, 0.7, 5):
                x, y = (k[e] * (1 - a) + k[w] * a).astype(int)
                if 0 <= y < v.shape[0] and 0 <= x < v.shape[1]:
                    vals.append(v[max(0, y - 2):y + 3, max(0, x - 2):x + 3].mean())
    return float(np.mean(vals)) if vals else None


def upright(k, s):
    """Shoulder-to-hip vector within 30 deg of vertical."""
    if (s[[5, 6, 11, 12]] < THR).any():
        return False
    d = k[[11, 12]].mean(0) - k[[5, 6]].mean(0)
    return d[1] > 0 and abs(np.degrees(np.arctan2(d[0], d[1]))) < 30


def box_area(k, s):
    p = k[s >= THR]
    if len(p) < 3:
        return 0.0
    w, h = p.max(0) - p.min(0)
    return float(w * h)


def same_body(k1, s1, k2, s2, scale):
    both = (s1 >= THR) & (s2 >= THR)
    if both.sum() < 5:
        return False
    return np.median(np.linalg.norm(k1[both] - k2[both], axis=1)) < 0.08 * scale


def is_referee(img, k, s, dark_v):
    tv = torso_darkness(img, k, s)
    av = forearm_brightness(img, k, s)
    return tv is not None and av is not None and tv < dark_v and tv < 0.65 * av and upright(k, s)


def _box(k, s):
    p = k[s >= THR] if (s >= THR).sum() >= 3 else k
    return np.r_[p.min(0), p.max(0)]


def _iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w * h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def select(img, kpts, scores, dark_v=70):
    order = np.argsort(-scores.mean(1))
    kpts, scores = kpts[order], scores[order]
    areas = np.array([box_area(k, s) for k, s in zip(kpts, scores)])
    keep, why = [], {"crowd": 0, "dup": 0, "ref": 0}
    for i, (k, s) in enumerate(zip(kpts, scores)):
        if areas.max() > 0 and areas[i] < 0.15 * areas.max():
            why["crowd"] += 1; continue
        scale = np.sqrt(max(areas[i], 1.0))
        if any(same_body(k, s, kpts[j], scores[j], scale) for j in keep):
            why["dup"] += 1; continue
        keep.append(i)
    # Referee/bystander: during a choke the two fighters overlap; the referee stands apart.
    # With 3+ candidates keep the most-overlapping pair (box IoU, ties -> higher score).
    # (A black-shirt colour rule was tried first and dropped fighters in shadow; see FINDINGS.md.)
    others = []
    if len(keep) > 2:
        boxes = {i: _box(kpts[i], scores[i]) for i in keep}
        best = max(((a, b) for x, a in enumerate(keep) for b in keep[x + 1:]),
                   key=lambda ab: (_iou(boxes[ab[0]], boxes[ab[1]]), -ab[0] - ab[1]))
        others = [i for i in keep if i not in best]
        why["ref"] += len(others)
        keep = list(best)
    why["ref_pts"] = [kpts[i] for i in others]
    why["kept_pts"] = [kpts[i] for i in keep]
    return kpts[keep], scores[keep], why


def track(frames_people, fps_eff, max_gap_s=0.5):
    """2 slots; Hungarian on mean joint distance; fill gaps up to max_gap_s."""
    slots, last_seen, out = [None, None], [-1e9, -1e9], []
    for t, (ks, ss) in enumerate(frames_people):
        assigned = [None, None]
        if len(ks):
            cost = np.full((len(ks), 2), 1e6)
            for i, (k, s) in enumerate(zip(ks, ss)):
                for j in range(2):
                    if slots[j] is not None:
                        pk, ps = slots[j]
                        m = (s >= THR) & (ps >= THR)
                        if m.any():
                            cost[i, j] = np.linalg.norm(k[m] - pk[m], axis=1).mean()
                    else:
                        cost[i, j] = 1e5
            r, c = linear_sum_assignment(cost)
            for i, j in zip(r, c):
                assigned[j] = (ks[i], ss[i]); slots[j] = (ks[i], ss[i]); last_seen[j] = t
        state = []
        for j in range(2):
            if assigned[j] is not None:
                state.append("seen")
            elif slots[j] is not None and (t - last_seen[j]) / fps_eff <= max_gap_s:
                state.append("filled")
            else:
                state.append("missing")
        out.append(state)
    return out


def upper_ok(s):
    return (s[UPPER] >= THR).sum() >= 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--score", type=float, default=0.3)
    ap.add_argument("--nms", type=float, default=0.65)
    ap.add_argument("--dark", type=float, default=70, help="HSV V below this = dark shirt")
    args = ap.parse_args()
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    sample_dir = ROOT / "data/pose/select2"; sample_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for clip in sorted(glob.glob(str(ROOT / "data/clips/*.mp4"))):
        name = Path(clip).stem
        cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or 30
        per_frame, raw_n, why_tot, i, saved = [], [], {"crowd": 0, "dup": 0, "ref": 0}, 0, 0
        while True:
            ok, img = cap.read()
            if not ok:
                break
            if i % args.every == 0:
                k, s = model(img, nms_thr=args.nms, score_thr=args.score)
                k = np.asarray(k).reshape(-1, 17, 2); s = np.asarray(s).reshape(-1, 17)
                raw_n.append(len(s))
                ks, ss, why = select(img, k, s, args.dark) if len(s) else (k, s, {})
                for w in ("crowd", "dup", "ref"):
                    why_tot[w] += why.get(w, 0)
                per_frame.append((ks, ss))
                if why.get("ref") and saved < 4:   # evidence: red = dropped as referee, green = kept fighters
                    vis = img.copy()
                    for pts, col in [(p, (0, 0, 255)) for p in why["ref_pts"]] + [(p, (0, 255, 0)) for p in why["kept_pts"]]:
                        for x, y in pts.astype(int):
                            cv2.circle(vis, (x, y), 9, col, -1)
                    cv2.imwrite(str(sample_dir / f"{name}_ref_{i}.jpg"), cv2.resize(vis, (640, 360))); saved += 1
            i += 1
        states = track(per_frame, fps / args.every)
        n = len(per_frame)
        two_seen = np.mean([st == ["seen", "seen"] for st in states])
        two_any = np.mean([all(x != "missing" for x in st) for st in states])
        two_upper = np.mean([len(ss) == 2 and all(upper_ok(x) for x in ss) for _, ss in per_frame])
        row = dict(clip=name, frames=n, every=args.every, score_thr=args.score, nms_thr=args.nms,
                   pct_raw_2plus=100 * np.mean(np.array(raw_n) >= 2),
                   pct_2_fighters_selected=100 * np.mean([len(ss) == 2 for _, ss in per_frame]),
                   pct_2_fighters_upper_ok=100 * two_upper,
                   pct_2_tracked_seen=100 * two_seen, pct_2_tracked_seen_or_filled=100 * two_any,
                   dropped=why_tot)
        results.append(row); print(json.dumps(row), flush=True)
    (ROOT / "research/pose_sweep/select2.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
