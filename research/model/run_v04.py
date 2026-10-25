"""MODEL_SPEC v0.4 check (owner batch 3): deep-lock two-on-one shrink (Q-D4), fatigue with a weak centered prior
only (C10 card dropped), and the two-part CONSCIOUSNESS gauge (G1 secs_to_out 7.5, G3 fast blood + slow fatigue).
Compares against v0.3; LOFO Brier, bootstrap, calibration, gauge check, Pantoja-Asakura trace.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python research/model/run_v04.py
"""
import math
from collections import defaultdict

import state_model as sm
from run_v03 import boot_diff, cards


def run(card_file, keep, fatigue=True):
    sm.USE_FATIGUE, sm.DEEP_TWO_ON_ONE_KEEP = fatigue, keep
    return sm.lofo(sm.load(), cards(card_file))


def round_gauges(rows, g=sm.CONSCIOUSNESS):
    """Consciousness at the end of each attempt, carrying blood deficit / lingering fatigue across attempts in the
    same round (both recover over the gap between attempts, blood fast, fatigue slowly)."""
    by = defaultdict(list)
    for r in rows:
        by[(r["fight_id"], r["round"])].append(r)
    out = {}
    for rs in by.values():
        B = D = 0.0
        prev_end = None
        for r in sorted(rs, key=lambda q: float(q["video_time_start"])):
            if prev_end is not None:
                gap = max(0.0, float(r["video_time_start"]) - prev_end)
                B *= math.exp(-gap / g["blood_recovery_secs"])
                D *= math.exp(-gap / g["fatigue_recovery_secs"])
            tr = sm.consciousness_trace(r, start=(B, D))
            _, c, B, D = tr[-1]
            out[id(r)] = (c, tr)
            prev_end = float(r["video_time_end"])
    return out


def main():
    sm.use_v04_gauge()   # this report is the v0.4 record (v0.4 squeeze + gauge)
    rows = sm.load()
    v03 = run("priors_owner.csv", 1.0)
    v04 = run("priors_owner_v04.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    v04_noshrink = run("priors_owner_v04.csv", 1.0)
    base = sm.lofo_base(rows)
    print(f"{len(rows)} attempts, {len({r['fight_id'] for r in rows})} fights, LOFO\n")
    print(f"{'model':40s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in {"always the average": base, "v0.3 (buckets + C10 card + fatigue)": v03,
                 "v0.4 without the deep-lock shrink": v04_noshrink, "v0.4 (shrink 25%, fatigue prior only)": v04}.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:40s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    for name, other in (("average", base), ("v0.3", v03)):
        m, ci = boot_diff(v04, other)
        print(f"v0.4 minus {name:8s}: {m:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]  (negative = v0.4 better)")
    print("\nCalibration, v0.4, at the 2-s landmark:")
    for lo, hi, n, mp, ob in sm.calib(v04):
        a, b = sm.wilson(round(ob * n), n)
        print(f"  {lo:.1f}-{min(hi, 1):.1f}  n={n:2d}  predicted {mp:.2f}  observed {ob:.2f}  [{a:.2f}, {b:.2f}]")

    sm.USE_FATIGUE, sm.DEEP_TWO_ON_ONE_KEEP = True, sm.DEEP_TWO_ON_ONE_KEEP_V04
    c = cards("priors_owner_v04.csv")
    beta = sm.fit(rows, c)
    print("\nCoefficients, all data (log-odds) [cards only]:")
    for n_, v, v0 in zip(["intercept (world)", "delta (sample)"] + sm.FEATS, beta, sm.fit([], c)):
        print(f"  {n_:18s} {v:+.2f} [{v0:+.2f}]")

    gauges = round_gauges(rows)
    fin = [gauges[id(r)][0] for r in rows if r["outcome"] in sm.SUCCESS]
    non = [gauges[id(r)][0] for r in rows if r["outcome"] not in sm.SUCCESS]
    auc = sum((a < b) + 0.5 * (a == b) for a in fin for b in non) / (len(fin) * len(non))
    print(f"\nConsciousness gauge at the end of the attempt (carried across a round): median finishes {sorted(fin)[len(fin) // 2]:.0f}, "
          f"non-finishes {sorted(non)[len(non) // 2]:.0f}; AUC (lower = finish) {auc:.2f}; "
          f"<= 20 at the end: finishes {sum(x <= 20 for x in fin)}/{len(fin)}, non-finishes {sum(x <= 20 for x in non)}/{len(non)}")

    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cov = sm.fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], c)
    tr = {round(t, 1): (cc, B, D) for t, cc, B, D in gauges[id(r)][1]}
    print("\nPantoja vs Asakura R2 (fight left out), on-screen values (real-world scale):")
    print(f"  {'t':>5s} {'finish':>7s} {'80% band':>10s} {'consc.':>7s} {'blood def.':>10s} {'ling. fat.':>10s} {'grip':>5s}")
    G = 0.0
    for a, b, x in sm.segments(r):
        if abs(a - round(a)) < 1e-6 or abs(a - 6.6) < 1e-6 or abs(a - 14.9) < 1e-6:
            lo, hi = sm.interval(bc, cov, x)
            cc, B, D = tr.get(round(a, 1), (float("nan"),) * 3)
            print(f"  {a:5.1f} {100 * sm.predict(bc, x, sample=False):6.0f}% {100 * lo:4.0f}-{100 * hi:3.0f}% {cc:7.0f} {B:10.1f} {D:10.1f} "
                  f"{100 * math.exp(-G / sm.FATIGUE_SCALE):5.0f}")
        G += (b - a) * sm.squeeze(x)
    print(f"  {sm.duration(r):5.1f}   100%  (unconscious: event shown; gauge snaps to 0)  grip {100 * math.exp(-G / sm.FATIGUE_SCALE):.0f}")
    print("\nConstants:", "DEEP_TWO_ON_ONE_KEEP =", sm.DEEP_TWO_ON_ONE_KEEP_V04, "| FATIGUE_SCALE =", sm.FATIGUE_SCALE,
          "| CONSCIOUSNESS =", sm.CONSCIOUSNESS)


if __name__ == "__main__":
    main()
