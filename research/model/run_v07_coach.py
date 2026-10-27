"""v0.7 + the BJJ coach review (research/coach_review/COACH_REVIEW.md §2) as priors on the weights.

    python research/model/run_v07_coach.py

The coach gives odds multipliers, not scenario %s, so they enter as the prior MEAN of each log-odds weight
(v0.7 shrinks every weight toward x1.0; here it shrinks toward the coach's number instead). Prior sd 0.7
log-odds ~ the coach's 80% ranges, about the weight of the evidence cards (coach: "weight them like n0 ~ 2").
Variants also try the coach's deep-lock rule (a two-on-one keeps 40% of its effect, not 25%).
The coach's numbers are AI-coach opinion, not data; the labels decide where they disagree.
"""
import csv
import math

import numpy as np

import model_v07 as m
import state_model as sm
from run_v03 import boot_diff

COACH = {"arm_under": 4.0, "grip_f4": 2.6, "grip_other": 1.9, "legs_bt": 1.6, "legs_hooks": 1.3, "two_on_one": 0.40,
         "chin_tucked": 0.85, "flattened": 2.5, "hand_tucked": 1.25, "fatigue": 0.6}
COACH_SD = 0.7
MU = np.zeros(2 + len(m.FEATS))
use_mu = False


def fit_cov(rows, cards):
    X, y, w = m.design(rows, cards)
    P = np.array([1 / 10 ** 2, 1 / m.RIDGE_SD ** 2] +
                 [1 / (COACH_SD if use_mu and f in COACH else m.RIDGE_BY.get(f, m.RIDGE_SD)) ** 2 for f in m.FEATS])
    mu = MU if use_mu else np.zeros_like(MU)
    beta = mu.copy()
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ beta))
        Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P)
        step = np.linalg.solve(Hm, X.T @ (w * (y - p)) - P * (beta - mu))
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    p = 1 / (1 + np.exp(-X @ beta))
    return beta, np.linalg.inv((X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P))


LEAN_DROP = ("legs_hooks", "chin_tucked")   # v0.8: factors the labels can't support yet are shrunk to no effect


def setup(coach=True, lean=True):
    """Install the coach-prior fit into model_v07 (also used by tools/mvp/demo.py). lean=True is model v0.8
    (explore_v08.py, 2026-10-28: leaner model, LOFO Brier 0.245 vs 0.249 for v0.7c on 71 attempts)."""
    global use_mu
    if lean:
        m.RIDGE_BY.update({f: 0.05 for f in LEAN_DROP})
        for f in LEAN_DROP:
            COACH.pop(f, None)
    for i, f in enumerate(m.FEATS):
        MU[2 + i] = math.log(COACH.get(f, 1.0))
    m.fit_cov = fit_cov
    m.fit = lambda rows, cards: fit_cov(rows, cards)[0]
    use_mu = coach


def main():
    global use_mu
    setup()
    rows = sm.load()
    m.D0.update(m.round_d0(rows))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    sm.USE_FATIGUE = False
    keep0 = sm.DEEP_TWO_ON_ONE_KEEP
    res = {"always the average": sm.lofo_base(rows)}
    use_mu = False; res["v0.7"] = m.lofo(rows, cards)
    use_mu = True; res["v0.7 + coach priors"] = m.lofo(rows, cards)
    sm.DEEP_TWO_ON_ONE_KEEP = 0.40; res["v0.7 + coach priors + coach deep-lock 40%"] = m.lofo(rows, cards)
    sm.DEEP_TWO_ON_ONE_KEEP = keep0
    print(f"{len(rows)} attempts, {len({r['fight_id'] for r in rows})} fights, leave-one-fight-out\n")
    print(f"{'model':44s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in res.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:44s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    for k in list(res)[2:]:
        d, ci = boot_diff(res[k], res["v0.7"])
        print(f"{k} minus v0.7: {d:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")

    use_mu = True
    beta, cov = fit_cov(rows, cards)
    print("\nWeights with coach priors, all data: odds multiplier (80% range) [coach]")
    for i, f in enumerate(m.FEATS):
        se = math.sqrt(cov[2 + i, 2 + i])
        print(f"  {f:14s} x{math.exp(beta[2 + i]):5.2f} ({math.exp(beta[2 + i] - 1.2816 * se):5.2f}-"
              f"{math.exp(beta[2 + i] + 1.2816 * se):5.2f})  [x{COACH.get(f, 1.0):.2f}]")

    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cv = fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], cards)
    print("\nPantoja vs Asakura (fight left out), v0.7 + coach priors:")
    for a, bb, x in m.segments(r):
        if abs(a - 6.6) < 1e-6 or abs(a - 14.9) < 1e-6 or a == 0 or abs(a - 10) < 1e-6:
            lo, hi = sm.interval(bc, cv, x)
            print(f"  {a:5.1f} s  {100 * sm.predict(bc, x, sample=False):3.0f}%  ({100 * lo:.0f}-{100 * hi:.0f}%)")


if __name__ == "__main__":
    main()
