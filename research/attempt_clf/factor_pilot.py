"""M2 pilot: can the computer see the choke factors itself? (2026-10-27)

    python -I research/attempt_clf/factor_pilot.py

Uses the cached detector features (CLIP fighter crop + past 2-4 s context, research/attempt_clf/) for every frame
inside a labeled attempt. The target is the factor's labeled value at that moment (the 2-s panel plus the G-panel
changes). Leave-one-fight-out logistic regression, as for the detector.
Reported per factor:
- frame ROC-AUC
- attempt-level agreement with the label at the 2-s landmark (mean score over the first 4 s of the attempt,
  threshold 0.5), as accuracy and Cohen's kappa, against always guessing the most common value
The roadmap's M2 bar is kappa >= 0.4 against the owner's labels.
"""
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.argv.append("--crop")
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
sys.path.insert(0, str(ROOT / "research/model"))
import attempt_clf as ac  # noqa: E402
import detector_v2 as d2  # noqa: E402
import state_model as sm  # noqa: E402

FACTORS = {   # name: (state key, positive values, negative values)
    "arm under the chin (vs over the jaw)": ("choke_arm_position", {"under_chin"}, {"over_jaw"}),
    "figure-four (vs any other grip)": ("rnc_style", {"figure_four"}, {"palm_to_palm", "gable", "wrist_pull", "short_choke", "one_arm"}),
    "body triangle (vs hooks / less)": ("control", {"body_triangle"}, {"two_hooks", "one_hook", "none"}),
    "defender 2-on-1 (vs not)": ("defender_two_on_one", {"True"}, {"False"}),
}


def main():
    clips = d2.aligned_clips()
    X, _, fight, clip, t = d2.load("_crop")
    X = d2.context(X, clip)
    rows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"]]
    by_clip = {}
    for r in rows:
        by_clip.setdefault(r["video_url"], []).append(r)
    # which attempt (and how far into it) each frame is
    att, el = np.full(len(t), -1), np.zeros(len(t))
    keyrows = []
    for ci, (name, _) in enumerate(clips):
        for r in by_clip.get(name, []):
            a, b = float(r["video_time_start"]), float(r["video_time_end"])
            m = (clip == ci) & (t >= a) & (t <= b)
            att[m], el[m] = len(keyrows), t[m] - a
            keyrows.append(r)
    inside = att >= 0
    print(f"{inside.sum()} frames inside {len(set(att[inside]))} attempts, {len(set(fight[inside]))} fights\n")
    out = []
    for fname, (key, pos, neg) in FACTORS.items():
        yv = np.full(len(t), -1)
        for k in np.where(inside)[0]:
            v = sm.state_at(keyrows[att[k]], el[k]).get(key, "")
            yv[k] = 1 if v in pos else 0 if v in neg else -1
        use = yv >= 0
        p = np.full(len(t), np.nan)
        for f in np.unique(fight[use]):
            te, tr = use & (fight == f), use & (fight != f)
            if len(np.unique(yv[tr])) < 2:
                continue
            clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced").fit(X[tr], yv[tr])
            p[te] = clf.predict_proba(X[te])[:, 1]
        ok = use & ~np.isnan(p)
        auc = roc_auc_score(yv[ok], p[ok]) if len(np.unique(yv[ok])) == 2 else float("nan")
        # attempt level: label at the landmark vs mean score over the first 4 s
        lab, pred = [], []
        for a_ in sorted(set(att[ok])):
            m = ok & (att == a_) & (el <= 4.0)
            if not m.any():
                continue
            v = sm.state_at(keyrows[a_], sm.LANDMARK).get(key, "")
            if v not in pos | neg:
                continue
            lab.append(int(v in pos)); pred.append(int(p[m].mean() >= 0.5))
        lab, pred = np.array(lab), np.array(pred)
        acc = (lab == pred).mean() if len(lab) else float("nan")
        base = max(lab.mean(), 1 - lab.mean()) if len(lab) else float("nan")
        kap = cohen_kappa_score(lab, pred) if len(set(lab)) > 1 else float("nan")
        out.append((fname, ok.sum(), yv[ok].mean(), auc, len(lab), acc, base, kap))
    print(f"{'factor':40s} {'frames':>6s} {'% pos':>6s} {'ROC':>5s} | {'attempts':>8s} {'acc':>5s} {'guess':>6s} {'kappa':>6s}")
    for f_, n, pp, auc, na, acc, base, kap in out:
        print(f"{f_:40s} {n:6d} {100 * pp:5.0f}% {auc:5.2f} | {na:8d} {acc:5.2f} {base:6.2f} {kap:6.2f}")


if __name__ == "__main__":
    main()
