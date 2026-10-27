"""Real attempt-detector scores for a demo clip (the 'BACK ATTACK DETECTED' indicator).

The clip is scored by detector v2 (CLIP fighter-crop features + past 2-4 s context + logistic regression) trained
on every OTHER fight only, the same leave-one-fight-out rule as the reported ROC-AUC 0.80, so the demo never
shows a detector that saw this fight. Uses the cached features (data/attempt_clf/), no video and no GPU.
Result: (times s, smoothed score 0-1) at 2 frames per second, cached to data/mvp/<clip>_det.npz.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TH_ON, TH_OFF, MIN_OFF = 0.55, 0.30, 2.0      # hysteresis: on above 0.55, off after 2 s below 0.30


def scores(clip_name, fight_id):
    cache = ROOT / "data/mvp" / f"{Path(clip_name).stem}_det.npz"
    if cache.exists():
        d = np.load(cache)
        return d["t"], d["p"]
    sys.path.insert(0, str(ROOT / "research/attempt_clf"))
    sys.argv.append("--crop") if "--crop" not in sys.argv else None
    import detector_v2 as d2
    from sklearn.linear_model import LogisticRegression
    X, y, fight, clip, _ = d2.load("_crop")
    tr = fight != fight_id
    clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced").fit(d2.context(X, clip)[tr], y[tr])
    c = np.load(ROOT / "data/attempt_clf/clips_crop" / f"{clip_name}.npz")
    p = clf.predict_proba(d2.context(c["X"], np.zeros(len(c["t"]), int)))[:, 1]
    p = np.convolve(p, np.ones(5) / 5, mode="same")                  # ~2 s smoothing
    np.savez_compressed(cache, t=c["t"], p=p)
    return c["t"], p


class Gate:
    """Turns the detector score into an on/off 'attempt detected' state (hysteresis, as in detector_events.py)."""

    def __init__(self, t, p):
        self.t, self.p, self.on, self.below = t, p, False, None

    def __call__(self, now):
        k = int(np.clip(np.searchsorted(self.t, now), 0, len(self.t) - 1))
        p = float(self.p[k])
        if not self.on and p >= TH_ON:
            self.on, self.below = True, None
        elif self.on:
            if p < TH_OFF:
                self.below = now if self.below is None else self.below
                if now - self.below >= MIN_OFF:
                    self.on = False
            else:
                self.below = None
        return self.on, p
