"""MODEL_SPEC v0.6 check: owner cards C1-C4 + evidence cards C5-C9 (research/priors_evidence, n0 2), evidence gauge
constants (secs_to_out 9, lingering 0.2, fatigue recovery 60 s, over-the-jaw 0.05, one arm 0.5), owner G2 kept.
Compared with v0.5; LOFO Brier, bootstrap, calibration, gauge tallies, Pantoja-Asakura trace.

    python research/model/run_v06.py
"""
import math

import calibrate_squeeze as cs
import state_model as sm
from run_v03 import boot_diff, cards
from run_v04 import round_gauges, run


def gauge_tally(rows):
    """Finishes whose consciousness first hits 0 within +-2 s of the labeled end; survivors that hit 0 / go below 20."""
    g = round_gauges(rows)
    hit = early = late = w0 = b20 = 0
    for r in rows:
        tr = g[id(r)][1]
        end = sm.duration(r)
        z = next((t for t, c, _, _ in tr if c <= 0), None)
        if r["outcome"] in sm.SUCCESS:
            if z is None:
                late += 1          # not out by the labeled end (snaps to 0 at the event)
            elif z < end - cs.TOL:
                early += 1
            else:
                hit += 1
        else:
            w0 += z is not None
            b20 += min(c for _, c, _, _ in tr) < 20
    nf = sum(r["outcome"] in sm.SUCCESS for r in rows)
    return f"finishes at 0 within 2 s before the end: {hit}/{nf} (early {early}, not by the end {late}); survivors at 0: {w0}/{len(rows) - nf} (below 20: {b20})"


def main():
    rows = sm.load()
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V05, sm.CONSCIOUSNESS_V05
    v05 = run("priors_owner_v04.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    t05 = gauge_tally(rows)
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    v06 = run("priors_v06.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    t06 = gauge_tally(rows)
    base = sm.lofo_base(rows)
    print(f"{'model (LOFO)':40s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in {"always the average": base, "v0.5 (owner cards C1-C4 + placeholders)": v05,
                 "v0.6 (owner C1-C4 + evidence C5-C9)": v06}.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:40s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    for name, other in (("v0.5", v05), ("average", base)):
        m, ci = boot_diff(v06, other)
        print(f"v0.6 minus {name:7s}: {m:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print("\nGauge (carried across a round, labeled end):\n  v0.5:", t05, "\n  v0.6:", t06)
    print("\nCalibration, v0.6, at the 2-s landmark:")
    for lo, hi, n, mp, ob in sm.calib(v06):
        a, b = sm.wilson(round(ob * n), n)
        print(f"  {lo:.1f}-{min(hi, 1):.1f}  n={n:2d}  predicted {mp:.2f}  observed {ob:.2f}  [{a:.2f}, {b:.2f}]")
    c = cards("priors_v06.csv")
    beta = sm.fit(rows, c)
    print("\nCoefficients, all data (log-odds) [cards only]:")
    for n_, v, v0 in zip(["intercept (world)", "delta (sample)"] + sm.FEATS, beta, sm.fit([], c)):
        print(f"  {n_:18s} {v:+.2f} [{v0:+.2f}]")

    gauges = round_gauges(rows)
    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cov = sm.fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], c)
    tr = {round(t, 1): cc for t, cc, _, _ in gauges[id(r)][1]}
    z = next((t for t, cc, _, _ in gauges[id(r)][1] if cc <= 0), None)
    print(f"\nPantoja vs Asakura R2 (fight left out), v0.6 on-screen values; consciousness first 0 at {z if z is None else round(z, 1)} s (out at 19.0 s):")
    print(f"  {'t':>5s} {'finish':>7s} {'80% band':>10s} {'squeeze':>8s} {'consc.':>7s} {'grip':>5s}")
    G = 0.0
    for a, b, x in sm.segments(r):
        if abs(a - round(a)) < 1e-6 or abs(a - 6.6) < 1e-6 or abs(a - 14.9) < 1e-6:
            lo, hi = sm.interval(bc, cov, x)
            print(f"  {a:5.1f} {100 * sm.predict(bc, x, sample=False):6.0f}% {100 * lo:4.0f}-{100 * hi:3.0f}% {sm.squeeze(x):8.2f} "
                  f"{tr.get(round(a, 1), float('nan')):7.0f} {100 * math.exp(-G / sm.FATIGUE_SCALE):5.0f}")
        G += (b - a) * sm.squeeze(x)
    print(f"  {sm.duration(r):5.1f}   100%  (unconscious: event shown)  consciousness just before {gauges[id(r)][1][-1][1]:.0f} -> 0;"
          f"  grip {100 * math.exp(-G / sm.FATIGUE_SCALE):.0f}")
    print("\nConstants: SQUEEZE =", sm.SQUEEZE_V06, "| CONSCIOUSNESS =", sm.CONSCIOUSNESS_V06,
          "| DEEP_TWO_ON_ONE_KEEP =", sm.DEEP_TWO_ON_ONE_KEEP_V04, "| FATIGUE_SCALE =", sm.FATIGUE_SCALE)


if __name__ == "__main__":
    main()
