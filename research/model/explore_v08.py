"""v0.8 exploration: principled variants of v0.7c, each scored leave-one-fight-out on the current labels.

    python research/model/explore_v08.py      -> research/model/explore_v08_output.txt (stdout)

Every variant is reported, not just the winner: with ~70 attempts, picking the best of several LOFO scores
overfits a little. A variant is only worth adopting if it is principled AND not worse; a clear win needs the 95% CI of
the difference to exclude 0.
Variants:
  A  v0.7c (baseline)
  B  re-attack term on (defender fatigue from earlier attempts in the round, card C15 only)
  C  leaner: drop the factors the labels can't support yet (both hooks, chin tucked)
  D  coach priors held tighter (sd 0.5) / E looser (sd 1.0)
  F  time left in the round as an adjustment (PREREG §5): defenders can stall to the bell
"""
import csv
import math

import numpy as np

import model_v07 as m
import run_v07_coach as rc
import state_model as sm
from run_v03 import boot_diff


def run(rows, cards, **kw):
    saved = (m.USE_REATTACK, rc.COACH_SD, list(m.FEATS))
    m.USE_REATTACK = kw.get("reattack", False)
    rc.COACH_SD = kw.get("sd", 0.7)
    try:
        return m.lofo(rows, cards)
    finally:
        m.USE_REATTACK, rc.COACH_SD = saved[0], saved[1]


def main():
    rc.setup()
    rows = sm.load()
    m.D0.update(m.round_d0(rows))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    sm.USE_FATIGUE = False
    res = {"always the average": sm.lofo_base(rows), "A v0.7c (baseline)": run(rows, cards)}
    res["B + re-attack term"] = run(rows, cards, reattack=True)
    # C: leaner model = the dropped factors get a near-zero prior sd (shrunk to no effect)
    saved_by = dict(m.RIDGE_BY)
    m.RIDGE_BY.update({"legs_hooks": 0.05, "chin_tucked": 0.05})
    saved_coach = dict(rc.COACH)
    for f in ("legs_hooks", "chin_tucked"):
        rc.COACH.pop(f, None)
    rc.setup()
    res["C leaner (no hooks / chin)"] = run(rows, cards)
    m.RIDGE_BY.clear(); m.RIDGE_BY.update(saved_by); rc.COACH.clear(); rc.COACH.update(saved_coach); rc.setup()
    res["D coach priors tighter (sd 0.5)"] = run(rows, cards, sd=0.5)
    res["E coach priors looser (sd 1.0)"] = run(rows, cards, sd=1.0)
    # F: time left in the round, as a small shift on the log-odds fitted on the labels (one extra coefficient)
    base = res["A v0.7c (baseline)"]
    tl = np.array([(300.0 - float(r["attempt_start_s"] or 150)) / 300.0 for _, _, _, r in base])
    y = np.array([a for a, _, _, _ in base])
    z = np.array([math.log(p / (1 - p)) for _, p, _, _ in base])
    fid = np.array([r["fight_id"] for _, _, _, r in base])
    pf = np.zeros(len(y))
    for f in np.unique(fid):                  # leave-one-fight-out for the extra coefficient too
        tr = fid != f
        g = 0.0
        for _ in range(50):                   # 1-D Newton, ridge 1
            p = 1 / (1 + np.exp(-(z[tr] + g * tl[tr])))
            g += (np.sum((y[tr] - p) * tl[tr]) - g) / (np.sum(p * (1 - p) * tl[tr] ** 2) + 1)
        pf[~tr] = 1 / (1 + np.exp(-(z[~tr] + g * tl[~tr])))
    res["F + time left in round (2-s score)"] = [(a, float(pp), s, r) for (a, _, s, r), pp in zip(base, pf)]
    print(f"{len(rows)} attempts, {len({r['fight_id'] for r in rows})} fights, leave-one-fight-out\n")
    print(f"{'variant':38s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in res.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:38s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    print()
    for k in list(res)[2:]:
        d, ci = boot_diff(res[k], res["A v0.7c (baseline)"])
        print(f"{k:38s} minus baseline: {d:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    d, ci = boot_diff(res["A v0.7c (baseline)"], res["always the average"])
    print(f"\nbaseline minus always-the-average: {d:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")


if __name__ == "__main__":
    main()
