"""Event-level check of the no-pose attempt detector (research/attempt_clf), as the finish model would consume it.

    C:/Users/netan/.venvs/clip/Scripts/python -I research/model/detector_events.py [--crop]

Frame scores (CLIP + logistic, leave-one-fight-out, same as attempt_clf.evaluate) -> ~2 s moving average ->
hysteresis (turn ON above th_on, OFF after 2 s below th_off) -> detected attempt windows. Then, per threshold:
- recall: share of labeled attempts that overlap a detected window
- on-time: share whose nearest detected window starts within 2 s of the labeled start (the model's landmark)
- good: on-time AND temporal overlap (IoU) >= 0.3, i.e. the window is that attempt, not the whole scramble
- false alarms per minute of non-attempt footage (detected windows touching no labeled attempt)
- median start delay (s)
Caveat: the clips are mostly attempt +- a few seconds, with only one fully watched no-RNC round, so the
false-alarm rate is measured on very little negative footage and is optimistic for full fights.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
import attempt_clf as ac  # noqa: E402

FPS = ac.FPS_S


def oof_scores(X, y, fight):
    from sklearn.linear_model import LogisticRegression
    p = np.full(len(y), np.nan)
    for f in np.unique(fight):
        te = fight == f
        if y[~te].min() == y[~te].max():
            continue
        clf = LogisticRegression(C=0.5, max_iter=2000, class_weight="balanced").fit(X[~te], y[~te])
        p[te] = clf.predict_proba(X[te])[:, 1]
    return p


def windows(ts, ps, th_on, th_off, min_off=2.0):
    out, start, below = [], None, None
    for t, p in zip(ts, ps):
        if start is None:
            if p >= th_on:
                start, below = t, None
        else:
            if p < th_off:
                below = t if below is None else below
                if t - below >= min_off:
                    out.append((start, below)); start, below = None, None
            else:
                below = None
    if start is not None:
        out.append((start, ts[-1]))
    return out


def main():
    d = np.load(ac.CACHE)
    X, y, fight, clip, t = d["X"], d["y"], d["fight"], d["clip"], d["t"]
    p = oof_scores(X, y, fight)
    ok = ~np.isnan(p)
    ps = ac.smooth(np.nan_to_num(p), clip, int(round(2 * FPS)) | 1)
    clips = sorted(ac.clips_and_windows().items())
    print(f"{len(clips)} clips; {ok.sum()} held-out frames; negative footage {((y == 0) & ok).sum() / FPS / 60:.1f} min")
    print(f"{'th_on':>5s} {'recall':>7s} {'on-time(|d|<=2s)':>16s} {'good(IoU>=.3,|d|<=2s)':>22s} {'false alarms/min neg':>21s} {'median delay s':>15s}")
    for th in (0.3, 0.4, 0.5, 0.6, 0.7):
        n_att = hit = ontime = good = fa = 0
        delays = []
        for ci, (name, info) in enumerate(clips):
            m = (clip == ci) & ok
            if not m.any():
                continue
            det = windows(t[m], ps[m], th, th - 0.15)
            for a, b in info["win"]:
                n_att += 1
                ov = [w for w in det if w[0] <= b and w[1] >= a]
                if ov:
                    hit += 1
                    w = min(ov, key=lambda w: abs(w[0] - a))
                    dl = w[0] - a
                    iou = (min(b, w[1]) - max(a, w[0])) / (max(b, w[1]) - min(a, w[0]))
                    delays.append(dl)
                    ontime += abs(dl) <= 2.0
                    good += abs(dl) <= 2.0 and iou >= 0.3
            fa += sum(1 for w in det if not any(w[0] <= b and w[1] >= a for a, b in info["win"]))
        neg_min = ((y == 0) & ok).sum() / FPS / 60
        print(f"{th:5.1f} {hit / n_att:7.2f} {ontime / n_att:16.2f} {good / n_att:22.2f} {fa / neg_min:21.2f} {np.median(delays) if delays else float('nan'):15.1f}")


if __name__ == "__main__":
    main()
