"""Geometry rule for back control (critique #1c): no training, just two skeletons.

For each ordering (A = possible attacker, D = defender), from 2D COCO keypoints:
  same_dir  cos of the two shoulder lines (left->right). Facing the same way = +1,
            facing each other (guard, mount) = -1.
  close     distance between torso centres / torso length.
  behind    how far A sits on D's *back* side. D's front = direction from D's
            shoulder midpoint to D's nose, perpendicular to D's spine; A's centre
            should be on the opposite side (positive = behind).
  head      distance from A's nose to D's shoulder midpoint / torso length
            (the attacker's head sits next to the defender's neck).
Back control fires if, for either ordering, same_dir > s, close < c, behind > b and
head < h. The attacker is the ordering with the larger `behind`.

Evaluation uses the same time-block folds as the classifier: thresholds are
picked by grid search on the training blocks and scored on the held-out block.

    python -I src/back_rule.py
"""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

import vicos_data

ROOT = Path(__file__).resolve().parents[1]
NOSE, L_SH, R_SH, L_HIP, R_HIP = 0, 5, 6, 11, 12
CONF_MIN = 0.2
DEFAULT = {"s": 0.3, "c": 1.0, "b": 0.0, "h": 1.0}
GRID = {"s": [0.0, 0.3, 0.6], "c": [0.6, 0.8, 1.0, 1.3], "b": [-0.1, 0.0, 0.1, 0.2],
        "h": [0.6, 0.8, 1.0, 1.5]}


def _unit(v):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-6)


def pair_geometry(poses):
    """poses [N, 2, 17, 3] -> dict of [N, 2] arrays; column a = athlete a as attacker."""
    xy = poses[..., :2].copy()
    xy[poses[..., 2] < CONF_MIN] = np.nan
    sh = (xy[:, :, L_SH] + xy[:, :, R_SH]) / 2
    hip = (xy[:, :, L_HIP] + xy[:, :, R_HIP]) / 2
    centre = (sh + hip) / 2
    spine = sh - hip
    torso = np.nanmean(np.linalg.norm(spine, axis=-1), axis=1)       # [N], both athletes
    shoulder_line = _unit(xy[:, :, R_SH] - xy[:, :, L_SH])
    front = xy[:, :, NOSE] - sh                                      # towards the face
    s_hat = _unit(spine)
    front = _unit(front - (front * s_hat).sum(-1, keepdims=True) * s_hat)

    out = {k: np.full((len(poses), 2), np.nan) for k in ("same_dir", "close", "behind", "head")}
    for a in range(2):
        d = 1 - a
        out["same_dir"][:, a] = (shoulder_line[:, a] * shoulder_line[:, d]).sum(-1)
        out["close"][:, a] = np.linalg.norm(centre[:, a] - centre[:, d], axis=-1) / torso
        out["behind"][:, a] = -((centre[:, a] - centre[:, d]) * front[:, d]).sum(-1) / torso
        out["head"][:, a] = np.linalg.norm(xy[:, a, NOSE] - sh[:, d], axis=-1) / torso
    return out


def apply_rule(g, p):
    with np.errstate(invalid="ignore"):
        fire = ((g["same_dir"] > p["s"]) & (g["close"] < p["c"]) &
                (g["behind"] > p["b"]) & (g["head"] < p["h"]))        # NaN -> False
    back = fire.any(1)
    attacker = np.where(np.nan_to_num(g["behind"][:, 0], nan=-9) >= np.nan_to_num(g["behind"][:, 1], nan=-9), 0, 1)
    return back, attacker


def fit_thresholds(g, y, idx):
    best, best_f1 = DEFAULT, -1
    sub = {k: v[idx] for k, v in g.items()}
    for vals in itertools.product(*GRID.values()):
        p = dict(zip(GRID, vals))
        f = f1_score(y[idx], apply_rule(sub, p)[0], zero_division=0)
        if f > best_f1:
            best, best_f1 = p, f
    return best


def binary_scores(y, pred, both):
    """Scores on all frames, plus recall on back frames where both athletes have a pose."""
    return {"recall": recall_score(y, pred, zero_division=0),
            "precision": precision_score(y, pred, zero_division=0),
            "f1": f1_score(y, pred, zero_division=0),
            "recall_both_visible": recall_score(y[both], pred[both], zero_division=0)}


def main():
    meta, poses = vicos_data.load()
    pos = meta["position"].to_numpy()
    y = np.isin(pos, ["back1", "back2"])
    g = pair_geometry(poses)
    both = ~np.isnan(poses[:, :, 0, 0]).any(1)

    pred_cv = np.zeros(len(y), dtype=bool)
    att_cv = np.zeros(len(y), dtype=int)
    chosen = []
    for tr, te in vicos_data.time_block_folds(meta):
        p = fit_thresholds(g, y, tr[::3])
        chosen.append(p)
        b, a = apply_rule({k: v[te] for k, v in g.items()}, p)
        pred_cv[te], att_cv[te] = b, a
    pred_def, att_def = apply_rule(g, DEFAULT)

    # back1/back2: which athlete is the attacker? Learn the suffix convention from the data.
    is_b1 = pos == "back1"
    hits = y & pred_cv
    agree = ((att_cv == 0) == is_b1)[hits].mean() if hits.any() else float("nan")
    role_acc = max(agree, 1 - agree)
    convention = "back1 = pose1 is behind" if agree >= 0.5 else "back1 = pose2 is behind"

    res = {"n_frames": int(len(y)), "n_back": int(y.sum()),
           "pct_back_frames_with_both_athletes": float(100 * (~np.isnan(poses[y][:, :, 0, 0])).all(1).mean()),
           "rule_cv_tuned": binary_scores(y, pred_cv, both),
           "rule_default_untuned": binary_scores(y, pred_def, both),
           "rule_role_accuracy_among_hits": float(role_acc), "suffix_convention": convention,
           "thresholds_per_fold": chosen}

    rows = [("Geometry rule, thresholds tuned on train blocks", res["rule_cv_tuned"]),
            ("Geometry rule, default thresholds (no tuning)", res["rule_default_untuned"])]
    for f in sorted((ROOT / "reports").glob("oof_*.csv")):
        o = pd.read_csv(f)
        yt = o["true"].isin(["back1", "back2"]).to_numpy()
        sc = binary_scores(yt, o["pred"].isin(["back1", "back2"]).to_numpy(), both[o["row"].to_numpy()])
        res[f.stem] = sc
        rows.append((f"Classifier `{f.stem.removeprefix('oof_')}` (18-class, back1|back2)", sc))

    out = ROOT / "reports"
    (out / "back_rule.json").write_text(json.dumps(res, indent=2, default=float))
    lines = ["# Back control: geometry rule vs classifier (VICOS, time-block folds)", "",
             f"{res['n_back']} back frames of {res['n_frames']}. Both athletes have a pose in "
             f"{res['pct_back_frames_with_both_athletes']:.0f}% of back frames (the rule can't fire otherwise).", "",
             "| Method | Back recall | Recall, both athletes visible | Precision | F1 |", "|---|---|---|---|---|"]
    lines += [f"| {n} | {s['recall']:.3f} | {s['recall_both_visible']:.3f} | {s['precision']:.3f} | {s['f1']:.3f} |"
              for n, s in rows]
    lines += ["", f"Rule picks the right attacker in {role_acc:.1%} of its correct back detections ({convention}).",
              "", "Caveat: every VICOS back frame comes from one session of one athlete pair, so none of these numbers "
              "show that back detection generalizes. The real test is hand-tagged UFC frames (critique #1a)."]
    (out / "back_rule.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
