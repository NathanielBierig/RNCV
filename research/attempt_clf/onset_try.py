"""One-off test: does a separate "choke is starting" model fix the detector's timing? (2026-10-26)

    C:/Users/netan/.venvs/clip/Scripts/python -I research/attempt_clf/onset_try.py

Onset model: positives = frames in [start, start + 3 s]; negatives = frames in [start - 8 s, start - 1 s]
(the exchange just before the choke). Trained leave-one-fight-out on the v2 context features (fighter crop).
The window detector then only opens when the v2 score is high AND the onset score is high; it stays open on v2.
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
sys.path.insert(0, str(ROOT / "research/model"))
import attempt_clf as ac  # noqa: E402
import detector_events as de  # noqa: E402
import detector_v2 as d2  # noqa: E402


def main():
    clips = sorted(ac.clips_and_windows().items())
    Xc, y, fight, clip, t = d2.load("_crop")
    X = d2.context(Xc, clip)
    on = np.full(len(y), -1)
    for ci, (name, info) in enumerate(clips):
        m = clip == ci
        for a, b in info["win"]:
            on[m & (t >= a) & (t <= a + 3)] = 1
            on[m & (t >= a - 8) & (t <= a - 1) & (on != 1)] = 0
    p_att = d2.oof(X, y, fight)
    p_on = np.full(len(y), np.nan)
    for f in np.unique(fight):
        te, tr = fight == f, (fight != f) & (on >= 0)
        if len(np.unique(on[tr])) < 2:
            continue
        clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced").fit(X[tr], on[tr])
        p_on[te] = clf.predict_proba(X[te])[:, 1]
    k = (on >= 0) & ~np.isnan(p_on)
    print(f"onset frames {np.sum(on == 1)}, pre-onset frames {np.sum(on == 0)}; onset vs just-before ROC-AUC "
          f"{roc_auc_score(on[k], p_on[k]):.2f} (v2 attempt score on the same frames: {roc_auc_score(on[k], p_att[k]):.2f})")
    ps = ac.smooth(np.nan_to_num(p_att), clip, 5)
    po = ac.smooth(np.nan_to_num(p_on), clip, 3)
    neg_min = (y == 0).sum() / ac.FPS_S / 60
    print(f"{'th':>4s} {'onset th':>8s} {'good':>5s} {'overlap':>7s} {'FA/min':>6s}")
    for th in (0.45, 0.5, 0.55, 0.6):
        for tho in (0.0, 0.5, 0.6, 0.7):
            n = good = hit = fa = 0
            for ci, (name, info) in enumerate(clips):
                m = clip == ci
                gate = np.where(po[m] >= tho, ps[m], np.minimum(ps[m], th - 0.01))
                det = de.windows(t[m], gate, th, th - 0.15)
                # keep a window open on the attempt score alone once started
                for a, b in info["win"]:
                    n += 1
                    ov = [w for w in det if w[0] <= b and w[1] >= a]
                    if ov:
                        hit += 1
                        w = min(ov, key=lambda w: abs(w[0] - a))
                        iou = (min(b, w[1]) - max(a, w[0])) / (max(b, w[1]) - min(a, w[0]))
                        good += abs(w[0] - a) <= 2.0 and iou >= 0.3
                fa += sum(1 for w in det if not any(w[0] <= b and w[1] >= a for a, b in info["win"]))
            print(f"{th:4.2f} {tho:8.1f} {good / n:5.2f} {hit / n:7.2f} {fa / neg_min:6.2f}")


if __name__ == "__main__":
    main()
