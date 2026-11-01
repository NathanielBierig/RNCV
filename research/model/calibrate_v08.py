"""Calibration of the finish model v0.8 (2026-11-01): the held-out calibration chart showed the low end too
pessimistic (model ~20%, observed ~45%).

    python research/model/calibrate_v08.py      -> research/model/calibrate_v08_output.txt (stdout)

1. Diagnose on the leave-one-fight-out (LOFO) predictions: fit logit(observed) = a + b * logit(predicted).
   b < 1 means the model is too spread out (too sure at both ends); a shifts everything.
2. Recalibrate honestly: for each fight, (a, b) are fitted on the OTHER fights' LOFO predictions only (nested), then
   applied to that fight. Compare Brier at the 2-s landmark and over every second, plus calibration by bin.
The recalibration is a display layer on top of v0.8 (it doesn't change the factor weights or the science).
"""
import csv
import math

import numpy as np

import model_v07 as m
import run_v07_coach as rc
import state_model as sm
from run_v03 import boot_diff


def logit(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def fit_ab(z, y, w=None, ridge=1.0):
    """Logistic regression of y on z (Newton), with a small ridge pulling (a, b) toward (0, 1)."""
    w = np.ones(len(y)) if w is None else w
    a, b = 0.0, 1.0
    for _ in range(100):
        p = 1 / (1 + np.exp(-(a + b * z)))
        g = np.array([np.sum(w * (y - p)) - ridge * a, np.sum(w * (y - p) * z) - ridge * (b - 1)])
        h = np.array([[np.sum(w * p * (1 - p)) + ridge, np.sum(w * p * (1 - p) * z)],
                      [np.sum(w * p * (1 - p) * z), np.sum(w * p * (1 - p) * z * z) + ridge]])
        step = np.linalg.solve(h, g)
        a, b = a + step[0], b + step[1]
        if np.abs(step).max() < 1e-10:
            break
    return a, b


def main():
    rc.setup()
    rows = sm.load()
    m.D0.update(m.round_d0(rows))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    sm.USE_FATIGUE = False
    preds = m.lofo(rows, cards)
    y = np.array([a for a, _, _, _ in preds])
    z = np.array([logit(p) for _, p, _, _ in preds])
    fid = np.array([r["fight_id"] for _, _, _, r in preds])
    a, b = fit_ab(z, y)
    print(f"{len(rows)} attempts, {len(set(fid))} fights. Diagnosis on all LOFO predictions: a = {a:+.2f}, b = {b:.2f}"
          f"  ({'too spread out' if b < 0.9 else 'too timid' if b > 1.1 else 'spread about right'};"
          f" {'shifted up' if a > 0.15 else 'shifted down' if a < -0.15 else 'no big shift'})\n")
    cal = []
    for (yy, p, segs, r), f in zip(preds, fid):
        tr = fid != f
        aa, bb = fit_ab(z[tr], y[tr])
        q = 1 / (1 + math.exp(-(aa + bb * logit(p))))
        segs_c = [(ww, 1 / (1 + math.exp(-(aa + bb * logit(pp))))) for ww, pp in segs]
        cal.append((yy, q, segs_c, r))
    base = sm.lofo_base(rows)
    print(f"{'model':34s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in (("always the average", base), ("v0.8", preds), ("v0.8 + recalibration (nested)", cal)):
        bl, bt, ll = sm.scores(v)
        print(f"{k:34s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    d, ci = boot_diff(cal, preds)
    print(f"\nrecalibrated minus v0.8: {d:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print("\nCalibration by bin (predicted -> observed), before | after:")
    edges = [0, 0.3, 0.5, 0.7, 1.0001]
    for lo, hi in zip(edges, edges[1:]):
        def cell(v):
            pp = np.array([p for _, p, _, _ in v]); yy = np.array([a for a, _, _, _ in v])
            k = (pp >= lo) & (pp < hi)
            return f"n={k.sum():2d} {pp[k].mean():.2f}->{yy[k].mean():.2f}" if k.any() else "  (none)      "
        print(f"  {lo:.1f}-{min(hi, 1):.1f}:  {cell(preds)}   |   {cell(cal)}")
    print(f"\nFor the app/demo: a = {a:.4f}, b = {b:.4f} (fitted on all LOFO predictions)")


if __name__ == "__main__":
    main()
