"""MODEL_SPEC v0.5 check (owner batch 4): v0.4 finish model and cards, with two squeeze presets feeding both the
CONSCIOUSNESS gauge and the attacker-fatigue term:
  v0.5      = owner-anchored (v0.4 weights + G2: locked under the chin + two-on-one = 0.9; secs_to_out 7.5) [default]
  v0.5-fit  = weights + secs_to_out fitted to the labels by calibrate_squeeze.py

    C:/Users/netan/.venvs/ufc-cv/Scripts/python -I research/model/run_v05.py
"""
import math

import state_model as sm
from run_v03 import boot_diff, cards
from run_v04 import round_gauges, run


def main():
    rows = sm.load()
    sm.use_v04_gauge()
    v04 = run("priors_owner_v04.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V05_FIT, sm.CONSCIOUSNESS_V05_FIT
    v05f = run("priors_owner_v04.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V05, sm.CONSCIOUSNESS_V05
    v05 = run("priors_owner_v04.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    base = sm.lofo_base(rows)
    print(f"{'model (LOFO)':34s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in {"always the average": base, "v0.4": v04, "v0.5-fit": v05f, "v0.5 (owner-anchored, default)": v05}.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:34s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    m, ci = boot_diff(v05, v04)
    print(f"v0.5 minus v0.4: {m:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    for name, sq, cg in (("v0.5-fit", sm.SQUEEZE_V05_FIT, sm.CONSCIOUSNESS_V05_FIT), ("v0.5", sm.SQUEEZE_V05, sm.CONSCIOUSNESS_V05)):
        sm.SQUEEZE, sm.CONSCIOUSNESS = sq, cg
        pa = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
        trp = round_gauges(rows)[id(pa)][1]
        z = next((t for t, cc, _, _ in trp if cc <= 0), None)
        print(f"  {name:9s} Pantoja consciousness: 10 s {trp[100][1]:.0f}, 14.9 s {trp[149][1]:.0f}, just before the KO {trp[-1][1]:.0f}; "
              f"first 0 at {z if z is None else round(z, 1)} s (out at 19.0 s)")
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V05, sm.CONSCIOUSNESS_V05

    c = cards("priors_owner_v04.csv")
    print(f"fatigue coefficient (all data): {sm.fit(rows, c)[-1]:+.2f} log-odds at full fatigue")
    gauges = round_gauges(rows)
    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cov = sm.fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], c)
    tr = {round(t, 1): (cc, B, D) for t, cc, B, D in gauges[id(r)][1]}
    print("\nPantoja vs Asakura R2 (fight left out), v0.5 (default) on-screen values:")
    print(f"  {'t':>5s} {'finish':>7s} {'80% band':>10s} {'squeeze':>8s} {'consc.':>7s} {'grip':>5s}")
    G = 0.0
    for a, b, x in sm.segments(r):
        if abs(a - round(a)) < 1e-6 or abs(a - 6.6) < 1e-6 or abs(a - 14.9) < 1e-6:
            lo, hi = sm.interval(bc, cov, x)
            cc = tr.get(round(a, 1), (float("nan"),))[0]
            print(f"  {a:5.1f} {100 * sm.predict(bc, x, sample=False):6.0f}% {100 * lo:4.0f}-{100 * hi:3.0f}% {sm.squeeze(x):8.2f} {cc:7.0f} "
                  f"{100 * math.exp(-G / sm.FATIGUE_SCALE):5.0f}")
        G += (b - a) * sm.squeeze(x)
    last = gauges[id(r)][1][-1]
    print(f"  {sm.duration(r):5.1f}   100%  (unconscious: event shown)  consciousness just before {last[1]:.0f} -> snaps to 0;"
          f"  grip {100 * math.exp(-G / sm.FATIGUE_SCALE):.0f}")
    print("\nConstants: SQUEEZE =", sm.SQUEEZE_V05, "| CONSCIOUSNESS =", sm.CONSCIOUSNESS_V05,
          "| DEEP_TWO_ON_ONE_KEEP =", sm.DEEP_TWO_ON_ONE_KEEP_V04, "| FATIGUE_SCALE =", sm.FATIGUE_SCALE)


if __name__ == "__main__":
    main()
