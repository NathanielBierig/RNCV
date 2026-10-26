"""MODEL_SPEC v0.3 check: owner bucket cards (C1-C4) + lower-weight placeholders (C5-C10) + attacker fatigue,
against the v0.2 placeholder cards. Leave-one-fight-out (LOFO) Brier, calibration, fight-cluster bootstrap,
and the Pantoja-Asakura trace (finish %, 80% band, Air, Grip).

    python research/model/run_v03.py
"""
import csv
import math
from pathlib import Path

import numpy as np

import state_model as sm

ROOT = Path(__file__).resolve().parents[2]


def cards(name):
    return list(csv.DictReader(open(ROOT / "research/model" / name, encoding="utf-8")))


def run(card_file, fatigue):
    sm.USE_FATIGUE = fatigue
    sm.DEEP_TWO_ON_ONE_KEEP = 1.0   # v0.3 had no deep-lock shrink; keeps this file reproducible after v0.4
    return sm.lofo(sm.load(), cards(card_file))


def sq_err(preds):
    return {(r["fight_id"], r["video_time_start"]): (y - p) ** 2 for y, p, _, r in preds}


def boot_diff(a, b, n=4000, seed=0):
    ka, kb = sq_err(a), sq_err(b)
    fights = sorted({k[0] for k in ka})
    d = {f: [ka[k] - kb[k] for k in ka if k[0] == f] for f in fights}
    rng = np.random.default_rng(seed)
    bs = [np.mean(sum((d[f] for f in rng.choice(fights, len(fights))), [])) for _ in range(n)]
    return float(np.mean(sum(d.values(), []))), np.percentile(bs, [2.5, 97.5])


def main():
    sm.use_v04_gauge()   # this report is the v0.3 record (v0.4 squeeze + gauge)
    rows = sm.load()
    res = {"v0.2 placeholders, no fatigue": run("priors_placeholder.csv", False),
           "v0.3 owner buckets, no fatigue": run("priors_owner.csv", False),
           "v0.3 owner buckets + fatigue": run("priors_owner.csv", True)}
    base = sm.lofo_base(rows)
    print(f"{len(rows)} attempts, {len({r['fight_id'] for r in rows})} fights, LOFO\n")
    print(f"{'model':34s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in {"always the average": base, **res}.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:34s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    best = res["v0.3 owner buckets + fatigue"]
    for name, other in (("average", base), ("v0.2 placeholders", res["v0.2 placeholders, no fatigue"]),
                        ("v0.3 no fatigue", res["v0.3 owner buckets, no fatigue"])):
        m, ci = boot_diff(best, other)
        print(f"v0.3+fatigue minus {name:18s}: {m:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  (negative = v0.3 better)")
    print("\nCalibration, v0.3 + fatigue, at the 2-s landmark:")
    for lo, hi, n, mp, ob in sm.calib(best):
        lo_ci, hi_ci = sm.wilson(round(ob * n), n)
        print(f"  {lo:.1f}-{min(hi, 1):.1f}  n={n:2d}  predicted {mp:.2f}  observed {ob:.2f}  [{lo_ci:.2f}, {hi_ci:.2f}]")

    sm.USE_FATIGUE = True
    sm.DEEP_TWO_ON_ONE_KEEP = 1.0
    c = cards("priors_owner.csv")
    beta = sm.fit(rows, c)
    b0 = sm.fit([], c)
    print("\nCoefficients, all data (log-odds) [cards only]:")
    for n_, v, v0 in zip(["intercept (world)", "delta (sample)"] + sm.FEATS, beta, b0):
        print(f"  {n_:18s} {v:+.2f} [{v0:+.2f}]")
    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cov = sm.fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], c)
    air = dict((round(t, 1), h) for t, h in sm.health_trace(r))
    print("\nPantoja vs Asakura R2 (fight left out), on-screen values (real-world scale):")
    print(f"  {'t':>5s} {'finish':>7s} {'80% band':>10s} {'air':>5s} {'grip':>5s}")
    G = 0.0
    for a, b, x in sm.segments(r):
        if abs(a - round(a)) < 1e-6 or abs(a - 6.5) < 1e-6 or abs(a - 14.5) < 1e-6:
            lo, hi = sm.interval(bc, cov, x)
            print(f"  {a:5.1f} {100 * sm.predict(bc, x, sample=False):6.0f}% {100 * lo:4.0f}-{100 * hi:3.0f}% "
                  f"{air.get(round(a, 1), float('nan')):5.0f} {100 * math.exp(-G / sm.FATIGUE_SCALE):5.0f}")
        G += (b - a) * sm.squeeze(x)
    print(f"  {sm.duration(r):5.1f}  100%  (unconscious: event shown)   air 0   grip {100 * math.exp(-G / sm.FATIGUE_SCALE):.0f}")


if __name__ == "__main__":
    main()
