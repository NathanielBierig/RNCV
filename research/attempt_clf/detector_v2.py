"""Attempt detector v2 experiments on the cached CLIP features (no new extraction, CPU, ~1 min).

    C:/Users/netan/.venvs/clip/Scripts/python -I research/attempt_clf/detector_v2.py

Same leave-one-fight-out protocol as attempt_clf.py / detector_events.py. Variants:
- frame: one frame's embedding (the v1 detector)
- +context: also the mean embedding over the past ~2 s and ~4 s, and the change vs the past 3 s
  ("the arm comes across" rather than "two men on the ground")
- full+crop: whole-frame and fighter-crop embeddings side by side
Each variant reports pooled ROC-AUC / PR-AUC (raw and ~2 s smoothed) and the event metrics of
detector_events.py at its best threshold. Every variant is listed, so the pick isn't hidden selection,
but with 19 fights the differences between close variants are noise-sized.
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
sys.path.insert(0, str(ROOT / "research/model"))
import attempt_clf as ac  # noqa: E402
import detector_events as de  # noqa: E402

FPS = ac.FPS_S


def load(tag):
    d = np.load(ROOT / f"data/attempt_clf/feats{tag}.npz")
    return d["X"], d["y"], d["fight"], d["clip"], d["t"]


def past_mean(X, clip, k):
    """Mean of the previous k frames (causal: usable live), per clip."""
    out = np.zeros_like(X)
    for c in np.unique(clip):
        idx = np.where(clip == c)[0]
        cs = np.cumsum(np.vstack([np.zeros((1, X.shape[1])), X[idx]]), 0)
        for j in range(len(idx)):
            lo = max(0, j - k)
            out[idx[j]] = (cs[j + 1] - cs[lo]) / (j + 1 - lo)
    return out


def context(X, clip):
    m2, m4, m3 = past_mean(X, clip, int(2 * FPS)), past_mean(X, clip, int(4 * FPS)), past_mean(X, clip, int(3 * FPS))
    return np.hstack([X, m2, m4, X - m3])


def oof(X, y, fight, C=0.5, pca=None):
    p = np.full(len(y), np.nan)
    for f in np.unique(fight):
        te = fight == f
        if y[~te].min() == y[~te].max():
            continue
        Xtr, Xte = X[~te], X[te]
        if pca:
            pc = PCA(pca, random_state=0).fit(Xtr)
            Xtr, Xte = pc.transform(Xtr), pc.transform(Xte)
        clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit(Xtr, y[~te])
        p[te] = clf.predict_proba(Xte)[:, 1]
    return p


def events(p, y, clip, t, clips):
    ps = ac.smooth(np.nan_to_num(p), clip, int(round(2 * FPS)) | 1)
    neg_min = (y == 0).sum() / FPS / 60
    best = None
    for th in np.arange(0.3, 0.86, 0.05):
        n = good = hit = fa = 0
        for ci, (name, info) in enumerate(clips):
            m = clip == ci
            if not m.any():
                continue
            det = de.windows(t[m], ps[m], th, th - 0.15)
            for a, b in info["win"]:
                n += 1
                ov = [w for w in det if w[0] <= b and w[1] >= a]
                if ov:
                    hit += 1
                    w = min(ov, key=lambda w: abs(w[0] - a))
                    iou = (min(b, w[1]) - max(a, w[0])) / (max(b, w[1]) - min(a, w[0]))
                    good += abs(w[0] - a) <= 2.0 and iou >= 0.3
            fa += sum(1 for w in det if not any(w[0] <= b and w[1] >= a for a, b in info["win"]))
        r = (good / n, hit / n, fa / neg_min, th)
        best = r if best is None or r[0] > best[0] else best
    return best


def main():
    clips = sorted(ac.clips_and_windows().items())
    Xf, y, fight, clip, t = load("")
    Xc = load("_crop")[0]
    Xb = load("_crop_b16")[0]
    variants = {
        "frame, crop (v1)": (Xc, {}),
        "frame, full": (Xf, {}),
        "frame, full+crop": (np.hstack([Xf, Xc]), {}),
        "+context, crop": (context(Xc, clip), {}),
        "+context, full+crop": (context(np.hstack([Xf, Xc]), clip), {}),
        "+context, full+crop, PCA 64": (context(np.hstack([Xf, Xc]), clip), {"pca": 64}),
        "+context, full+crop+b16, PCA 64": (context(np.hstack([Xf, Xc, Xb]), clip), {"pca": 64}),
        "+context, full+crop, C 0.05": (context(np.hstack([Xf, Xc]), clip), {"C": 0.05}),
    }
    print(f"{len(np.unique(fight))} fights, {len(y)} frames, base rate {y.mean():.2f}\n")
    print(f"{'variant':34s} {'ROC':>5s} {'ROC sm':>6s} {'PR':>5s} {'PR sm':>6s} | {'good win':>8s} {'overlap':>7s} {'FA/min':>6s} {'th':>4s}")
    for k, (X, kw) in variants.items():
        p = oof(X, y, fight, **kw)
        ok = ~np.isnan(p)
        ps = ac.smooth(np.nan_to_num(p), clip, 5)
        g, h, fa, th = events(p, y, clip, t, clips)
        print(f"{k:34s} {roc_auc_score(y[ok], p[ok]):5.2f} {roc_auc_score(y[ok], ps[ok]):6.2f} "
              f"{average_precision_score(y[ok], p[ok]):5.2f} {average_precision_score(y[ok], ps[ok]):6.2f} | "
              f"{g:8.2f} {h:7.2f} {fa:6.2f} {th:4.2f}", flush=True)


if __name__ == "__main__":
    main()
