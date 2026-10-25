"""v0.5: calibrate the CONSCIOUSNESS gauge's squeeze weights and secs_to_out from the labels (owner batch 4).

    C:/Users/netan/.venvs/ufc-cv/Scripts/python research/model/calibrate_squeeze.py

Fixed by the owner (G2): figure-four locked under the chin WITH a two-on-one = 0.9 of a full squeeze.
Fitted (weak priors at the v0.4 values): w_jaw (arm over the jaw), w_one_arm (under the chin, no lock),
chin_relief (share of squeeze a tucked chin takes away), secs_to_out (seconds of full squeeze to "out").
Target: a finished attempt's gauge reaches 0 at its labeled end; a survived attempt's gauge stays above 20.
The gauge is simulated per state segment in closed form (blood deficit B, lingering fatigue D; v0.4 rules),
carried across attempts in the same round. Scored leave-one-fight-out, then refit on all fights.
"""
import math
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize

import state_model as sm

V04 = {"w_jaw": 0.15, "w_one_arm": 0.45, "chin_relief": 0.30, "secs_to_out": 7.5}
NAMES = list(V04)
# v0.6 (--evidence): priors from research/priors_evidence/gauge_evidence.csv (center, 90% range -> sd on the fit scale)
EVIDENCE = {"w_jaw": 0.05, "w_one_arm": 0.50, "chin_relief": 0.30, "secs_to_out": 9.0}
EVIDENCE_RANGE = {"w_jaw": (0.01, 0.20), "w_one_arm": (0.30, 0.70), "chin_relief": (0.10, 0.50), "secs_to_out": (7.0, 11.0)}
EVIDENCE_GAUGE = dict(sm.CONSCIOUSNESS_V04, secs_to_out=9.0, lingering_share=0.2, fatigue_recovery_secs=60.0)
PRIOR_CENTER = V04
TWO_RELIEF_OPEN = 0.35       # two-on-one relief when the choke is not locked under the chin (unchanged)
TWO_RELIEF_LOCKED = 0.10     # owner G2: locked under the chin + two-on-one = 0.9 of full
HAND_BONUS = 0.15            # unchanged
G = sm.CONSCIOUSNESS_V04     # recovery constants (v0.5: v0.4 values; v0.6 --evidence: EVIDENCE_GAUGE); secs_to_out is fitted
TOL = 2.0                    # "hits 0 within +-2 s of the labeled end"
SURVIVOR_MAX = 0.8           # survivors should stay at consciousness >= 20 (deficit <= 80%)
TAP_MAX = 40.0               # tap-aware target: a tap comes when he feels it going, i.e. consciousness <= 40 at the tap
MODE = {"tap_aware": False, "survivor_weight": 4.0, "chin_keep_locked": 1.0}


def squeeze(x, p):
    """v0.5 squeeze strength 0..1 (sm.squeeze with the fixed v0.5 parts and the candidate fitted weights p)."""
    return sm.squeeze(x, dict(sm.SQUEEZE_V05, w_jaw=p["w_jaw"], w_one_arm=p["w_one_arm"], chin_relief=p["chin_relief"],
                              two_relief_open=TWO_RELIEF_OPEN, two_relief_locked=TWO_RELIEF_LOCKED, hand_bonus=HAND_BONUS,
                              chin_keep_locked=MODE["chin_keep_locked"]))


def prepare(rows):
    """Per round: attempts in order, each = (row, gap before it, [(seconds, x)])."""
    by = defaultdict(list)
    for r in rows:
        by[(r["fight_id"], r["round"])].append(r)
    rounds = []
    for rs in by.values():
        rs = sorted(rs, key=lambda q: float(q["video_time_start"]))
        out, prev = [], None
        for r in rs:
            gap = 0.0 if prev is None else max(0.0, float(r["video_time_start"]) - prev)
            out.append((r, gap, [(b - a, x) for a, b, x in sm.segments(r)]))
            prev = float(r["video_time_end"])
        rounds.append(out)
    return rounds


def simulate(rounds, p):
    """Per attempt: (row, t0 = first time consciousness hits 0 (or extrapolated past the end), max deficit share)."""
    S, share = p["secs_to_out"], G["lingering_share"]
    res = []
    for rnd in rounds:
        B = D = 0.0
        for r, gap, segs in rnd:
            B *= math.exp(-gap / G["blood_recovery_secs"])
            D *= math.exp(-gap / G["fatigue_recovery_secs"])
            t, t0, fmax, s_last = 0.0, None, (B + D) / S, 0.0
            for L, x in segs:
                s = squeeze(x, p)
                if s >= G["light_below"]:
                    if t0 is None and B + D + s * L >= S:
                        t0 = t + (S - B - D) / s
                    B += (1 - share) * s * L
                    D += share * s * L
                else:
                    be, de = (1 - share) * s * G["blood_recovery_secs"], share * s * G["fatigue_recovery_secs"]
                    B = be + (B - be) * math.exp(-L / G["blood_recovery_secs"])
                    D = de + (D - de) * math.exp(-L / G["fatigue_recovery_secs"])
                    if t0 is None and B + D >= S:
                        t0 = t + L
                fmax = max(fmax, (B + D) / S)
                t += L
                s_last = s
            if t0 is None:                                   # not out by the end: when would he be, at the last squeeze?
                t0 = t + (S - B - D) / s_last if s_last >= G["light_below"] else t + 30.0
            res.append((r, t, t0, fmax))
    return res


def loss(theta, rounds):
    p = dict(zip(NAMES, theta_to_p(theta)))
    L = 0.0
    for r, end, t0, fmax in simulate(rounds, p):
        if r["outcome"] == "tap" and MODE["tap_aware"]:
            S = p["secs_to_out"]
            short = max(0.0, (1 - TAP_MAX / 100) - f_end_of(r, end, t0, p)) * S   # seconds of squeeze missing to reach 40
            L += short * short / 4 if short <= 2 else short - 1
        elif r["outcome"] in sm.SUCCESS:
            e = min(abs(t0 - end), 20.0)
            L += e * e / 4 if e <= 2 else e - 1               # Huber in seconds (quadratic within the +-2 s target)
        else:
            ex = max(0.0, fmax - SURVIVOR_MAX) * p["secs_to_out"]
            L += MODE["survivor_weight"] * ex * ex            # seconds of squeeze beyond the 80% line
    prior = sum(((t - t0) / sd) ** 2 for t, t0, sd in zip(theta, p_to_theta(PRIOR_CENTER), PRIOR_SD))
    return L + prior


# parameters on an unbounded scale: logit for 0..1 weights, log for seconds; weak priors at the v0.4 values
def p_to_theta(p):
    lg = lambda v: math.log(v / (1 - v))
    return [lg(p["w_jaw"]), lg(p["w_one_arm"]), lg(p["chin_relief"]), math.log(p["secs_to_out"])]


def theta_to_p(t):
    sg = lambda v: 1 / (1 + math.exp(-v))
    return [sg(t[0]), sg(t[1]), sg(t[2]), math.exp(t[3])]


PRIOR_SD = [1.0, 1.0, 1.0, 0.25]   # logit sd 1 = weak; log sd 0.25 keeps secs_to_out roughly inside the owner's 5-10 s


def fit(rounds):
    best = None
    for start in (p_to_theta(PRIOR_CENTER), [-1.0, 0.5, -0.5, math.log(9)], [-2.5, -0.5, -1.5, math.log(6)]):
        r = minimize(loss, start, args=(rounds,), method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-3, "maxiter": 4000})
        if best is None or r.fun < best.fun:
            best = r
    return dict(zip(NAMES, theta_to_p(best.x)))


def f_end_of(r, end, t0, p):
    """Deficit share at the labeled end, recovered from the zero time (linear in the last squeeze; >= 1 if already out)."""
    return 1.0 if t0 <= end else max(0.0, 1 - (t0 - end) / max(p["secs_to_out"], 1e-6))


def tally_taps(res, p):
    taps = [(end, t0) for r, end, t0, _ in res if r["outcome"] == "tap"]
    ok = sum(100 * (1 - f_end_of(None, end, t0, p)) <= TAP_MAX for end, t0 in taps)
    return f"taps with consciousness <= {TAP_MAX:.0f} at the tap: {ok}/{len(taps)}"


def tally(res):
    fin = [(r, end, t0) for r, end, t0, _ in res if r["outcome"] in sm.SUCCESS]
    sur = [(r, fmax) for r, _, _, fmax in res if r["outcome"] not in sm.SUCCESS]
    hit = sum(abs(t0 - end) <= TOL for _, end, t0 in fin)
    early = sum(t0 < end - TOL for _, end, t0 in fin)
    late = sum(t0 > end + TOL for _, end, t0 in fin)
    wrong0 = sum(f >= 1.0 for _, f in sur)
    below20 = sum(f > SURVIVOR_MAX for _, f in sur)
    return hit, early, late, len(fin), wrong0, below20, len(sur)


def fmt(t):
    hit, early, late, nf, w0, b20, ns = t
    return (f"finishes at 0 within +-2 s of the end: {hit}/{nf} (early {early}, late {late}); "
            f"survivors wrongly at 0: {w0}/{ns} (below 20: {b20}/{ns})")


def main():
    import sys
    if "--tap-aware" in sys.argv:
        MODE.update(tap_aware=True, survivor_weight=1.0)
        print("MODE: tap-aware (unconscious -> 0 at the end; tap -> consciousness <= 40 at the tap; survivors >= 20, weight 1)")
    if "--evidence" in sys.argv:
        global PRIOR_CENTER, PRIOR_SD, G
        lg = lambda v: math.log(v / (1 - v))
        PRIOR_CENTER, G = EVIDENCE, EVIDENCE_GAUGE
        PRIOR_SD = [(lg(EVIDENCE_RANGE[k][1]) - lg(EVIDENCE_RANGE[k][0])) / 3.29 for k in NAMES[:3]] +                    [(math.log(EVIDENCE_RANGE["secs_to_out"][1]) - math.log(EVIDENCE_RANGE["secs_to_out"][0])) / 3.29]
        print("EVIDENCE priors (v0.6):", EVIDENCE, "sd", [round(v, 2) for v in PRIOR_SD], "| gauge", EVIDENCE_GAUGE)
    if "--chin-rule" in sys.argv:
        MODE["chin_keep_locked"] = 0.25
        print("CHIN RULE: once the choke is locked under the chin, a tucked chin keeps 25% of its relief (v0.5b)")
    if "--tap-aware" not in sys.argv:
        print("MODE: owner's target (every finish -> 0 at the end; survivors >= 20, weight 4)")
    rows = sm.load()
    sm.USE_FATIGUE = False
    rounds = prepare(rows)
    print(f"{len(rows)} attempts ({sum(r['outcome'] in sm.SUCCESS for r in rows)} finishes), {len(rounds)} rounds\n")
    # v0.4 squeeze (two-on-one relief 0.35 everywhere, softened only by the deep-lock shrink) for 'before'
    v04_res = simulate_v04(rounds)
    print("BEFORE (v0.4 constants):     ", fmt(tally(v04_res)))
    print("prior constants, no fit:     ", fmt(tally(simulate(rounds, PRIOR_CENTER))))

    lofo_res, fits = [], []
    fights = sorted({r["fight_id"] for r in rows})
    for f in fights:
        tr = [rnd for rnd in rounds if rnd[0][0]["fight_id"] != f]
        te = [rnd for rnd in rounds if rnd[0][0]["fight_id"] == f]
        p = fit(tr)
        fits.append(p)
        lofo_res += simulate(te, p)
    print("AFTER, leave-one-fight-out:  ", fmt(tally(lofo_res)))
    print("   ", tally_taps(lofo_res, fit(rounds)))
    p_all = fit(rounds)
    print("AFTER, refit on all (in-sample):", fmt(tally(simulate(rounds, p_all))))
    print("\nFitted constants (all fights) [prior] (LOFO range):")
    for k in NAMES:
        vals = [q[k] for q in fits]
        print(f"  {k:12s} {p_all[k]:.3f}  [prior {PRIOR_CENTER[k]}]  ({min(vals):.3f}-{max(vals):.3f})")
    print("  fixed: two-on-one relief", TWO_RELIEF_OPEN, "open /", TWO_RELIEF_LOCKED, "locked under chin; hand bonus", HAND_BONUS)

    print("\nPer finish (LOFO): labeled end vs time the gauge hits 0")
    for r, end, t0, fmax in lofo_res:
        if r["outcome"] in sm.SUCCESS:
            print(f"  {r['attacker'][:18]:18s} {r['outcome']:12s} end {end:5.1f}s  zero at {t0:5.1f}s  ({t0 - end:+.1f})")
    print("Survivors that reach 0 or below 20 (LOFO):")
    for r, end, t0, fmax in lofo_res:
        if r["outcome"] not in sm.SUCCESS and fmax > SURVIVOR_MAX:
            print(f"  {r['attacker'][:18]:18s} {r['outcome']:15s} dur {end:5.1f}s  min consciousness {100 * max(0, 1 - fmax):3.0f}")

    pa = [x for x in lofo_res if x[0]["video_url"].startswith("pantoja_asakura")][0]
    print(f"\nPantoja-Asakura (fight left out): zero at {pa[2]:.1f}s, out at {pa[1]:.1f}s (v0.4: 16 s)")
    return p_all


def simulate_v04(rounds):
    """The v0.4 gauge exactly (v0.4 squeeze, secs_to_out 7.5), for the 'before' numbers."""
    saved = sm.SQUEEZE, sm.CONSCIOUSNESS
    sm.use_v04_gauge()
    res = []
    for rnd in rounds:
        B = D = 0.0
        for r, gap, segs in rnd:
            g4 = sm.CONSCIOUSNESS_V04
            B *= math.exp(-gap / g4["blood_recovery_secs"]); D *= math.exp(-gap / g4["fatigue_recovery_secs"])
            tr = sm.consciousness_trace(r, start=(B, D))
            _, _, B, D = tr[-1]
            t0 = next((t for t, c, _, _ in tr if c <= 0), None)
            fmax = max((b + d) / g4["secs_to_out"] for _, _, b, d in tr)
            end = sm.duration(r)
            res.append((r, end, t0 if t0 is not None else end + 30, fmax))
    sm.SQUEEZE, sm.CONSCIOUSNESS = saved
    return res


if __name__ == "__main__":
    main()
