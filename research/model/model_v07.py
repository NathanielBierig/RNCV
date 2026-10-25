"""RNCV finish model v0.7 (MODEL_SPEC §4f): owner's structural review of the v0.6 weights.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python research/model/model_v07.py

Changes vs v0.6 (same expert-prior logistic state model, same cards-as-pretend-data method; state_model.py is reused):
1. Grip by type: grip_f4 (figure-four) and grip_other (palm-to-palm / gable / wrist pull), both vs unlocked
   (one arm / short choke). Cards put them in the owner's order: figure-four > other locks > one arm.
2. Choking hand tucked: mainly through the defender's hands (in a lock under the chin, a hidden hand cuts the
   two-on-one's effect to 25%, the v0.4 deep-lock rule), plus a small own effect with a tight prior (sd 0.5),
   so it can't reach v0.6's x1.7 without strong data. (Dropping the own effect entirely cost Brier +0.012.)
3. Legs split: legs_bt (body triangle) and legs_hooks (two hooks), both vs one hook / none; the body triangle
   gets the stronger card.
4. Re-attacks: def_fatigue = 1 - exp(-D0 / 1 s), D0 = the defender's lingering fatigue carried over from earlier
   attempts in the same round (CONSCIOUSNESS gauge, v0.6 constants), constant within the attempt. The labels can't
   test it (a finish-list round always ends with its finish, so later attempts "finish more" by construction), so
   it is learned from the card only: label rows see def_fatigue = 0 (DEF_FAT_FROM_LABELS = False).
   USE_REATTACK = False (default, recommended for MVP 0.2) leaves the term out until random-fight rounds can test it;
   main() reports both.
5. Kept: arm under the chin, flattened, two-on-one (deep-lock rule), chin tucked, attacker fatigue, 9-s gauge.
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import state_model as sm

HERE = Path(__file__).resolve().parent
FEATS = ["arm_under", "grip_f4", "grip_other", "legs_bt", "legs_hooks", "two_on_one", "chin_tucked", "flattened",
         "def_fatigue", "hand_tucked", "fatigue"]
OTHER_LOCKS = {"palm_to_palm", "gable", "wrist_pull"}
UNKNOWN_GRIP = (0.5, 0.2)        # unclear / blank grip: ~the labeled shares of figure-four and other locks
UNKNOWN_LEGS = (0.25, 0.25)      # unclear / blank legs: halfway between strong and weak, split BT / hooks
DEF_FAT_SCALE = 1.0              # seconds of lingering fatigue for def_fatigue = 0.63
DEF_FAT_FROM_LABELS = False      # see docstring, point 4
RIDGE_SD = 1.5
RIDGE_BY = {"hand_tucked": 0.5}  # per-feature prior sd on the log-odds (tighter = shrunk toward no effect)
USE_REATTACK = False             # see docstring, point 4


def b(v):
    return {"True": 1.0, "False": 0.0}.get(v, 0.5)


def encode(st, fat=0.0, dfat=0.0):
    arm = {"under_chin": 1.0, "over_jaw": 0.0}.get(st.get("choke_arm_position", ""), 0.5)
    g = st.get("rnc_style", "")
    f4, other = (1.0, 0.0) if g == "figure_four" else (0.0, 1.0) if g in OTHER_LOCKS else \
        (0.0, 0.0) if g in sm.OPEN else UNKNOWN_GRIP
    c = st.get("control", "")
    bt, hooks = (1.0, 0.0) if c == "body_triangle" else (0.0, 1.0) if c == "two_hooks" else \
        (0.0, 0.0) if c in ("one_hook", "none") else UNKNOWN_LEGS
    hand = b(st.get("choking_hand_tucked", ""))
    two = b(st.get("defender_two_on_one", "")) * (1 - (1 - sm.DEEP_TWO_ON_ONE_KEEP) * arm * (f4 + other) * hand)
    return np.array([arm, f4, other, bt, hooks, two, b(st.get("chin_tucked", "")), b(st.get("opponent_flattened", "")),
                     dfat, hand, fat])


def round_d0(rows):
    """Lingering defender fatigue D (seconds) at the start of each attempt, carried across the round (v0.6 gauge)."""
    g = sm.CONSCIOUSNESS_V06
    saved = sm.SQUEEZE, sm.CONSCIOUSNESS
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    by = defaultdict(list)
    for r in rows:
        by[(r["fight_id"], r["round"])].append(r)
    out = {}
    for rs in by.values():
        B = D = 0.0
        prev = None
        for i, r in enumerate(sorted(rs, key=lambda q: float(q["video_time_start"]))):
            if prev is not None:
                gap = max(0.0, float(r["video_time_start"]) - prev)
                B *= math.exp(-gap / g["blood_recovery_secs"])
                D *= math.exp(-gap / g["fatigue_recovery_secs"])
            out[key(r)] = (D, i + 1)
            _, _, B, D = sm.consciousness_trace(r, start=(B, D))[-1]
            prev = float(r["video_time_end"])
    sm.SQUEEZE, sm.CONSCIOUSNESS = saved
    return out


def key(r):
    return r["fight_id"], r["round"], r["video_time_start"]


D0 = {}


def dfat_of(r):
    if not USE_REATTACK:
        return 0.0
    return 1 - math.exp(-D0.get(key(r), (0.0, 1))[0] / DEF_FAT_SCALE)


def segments(r, dfat=None):
    """Like sm.segments (0.5-s grid, attacker fatigue from squeeze effort), with the v0.7 feature vector.
    Squeeze strength still comes from the v0.6 gauge on the v0.6 encoding (its weights are unchanged)."""
    dfat = dfat_of(r) if dfat is None else dfat
    dur = sm.duration(r)
    cuts = sorted({0.0, dur, *[t for t, _, _ in sm.changes(r) if 0 < t < dur], *np.arange(sm.GRID, dur, sm.GRID).round(3)})
    out, G = [], 0.0
    for a, bb in zip(cuts, cuts[1:]):
        if bb <= a:
            continue
        st = sm.state_at(r, a)
        out.append((a, bb, encode(st, 1 - math.exp(-G / sm.FATIGUE_SCALE), dfat)))
        G += (bb - a) * sm.squeeze(sm.encode(st), sm.SQUEEZE_V06)
    return out


def x_at(r, t):
    segs = segments(r)
    return next((x for a, bb, x in segs if a <= t < bb), segs[-1][2])


def design(rows, cards):
    X, y, w = [], [], []
    for r in rows:
        dur, yy = sm.duration(r), float(r["outcome"] in sm.SUCCESS)
        for a, bb, x in segments(r, None if DEF_FAT_FROM_LABELS else 0.0):
            X.append(np.r_[1.0, sm.selected(r), x]); y.append(yy); w.append((bb - a) / dur)
    for c in cards:
        if not USE_REATTACK and float(c.get("def_fatigue") or 0):
            continue
        x = np.r_[1.0, 0.0, [float(c.get(f) or 0) for f in FEATS]]
        n0, pc = sm.card_weight(c), sm.card_p(c)
        for yy, ww in ((1.0, pc * n0), (0.0, (1 - pc) * n0)):
            X.append(x); y.append(yy); w.append(ww)
    return np.array(X), np.array(y), np.array(w)


def fit_cov(rows, cards):
    X, y, w = design(rows, cards)
    P = np.array([1 / 10 ** 2, 1 / RIDGE_SD ** 2] + [1 / RIDGE_BY.get(f, RIDGE_SD) ** 2 for f in FEATS])
    beta = np.zeros(X.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-X @ beta))
        Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P)
        step = np.linalg.solve(Hm, X.T @ (w * (y - p)) - P * beta)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    p = 1 / (1 + np.exp(-X @ beta))
    Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P)
    return beta, np.linalg.inv(Hm)


def fit(rows, cards):
    return fit_cov(rows, cards)[0]


def lofo(rows, cards):
    out = []
    for fid in sorted({r["fight_id"] for r in rows}):
        beta = fit([r for r in rows if r["fight_id"] != fid], cards)
        for r in rows:
            if r["fight_id"] == fid:
                dur = sm.duration(r)
                pl = sm.predict(beta, x_at(r, min(sm.LANDMARK, dur)))
                segs = [((bb - a) / dur, sm.predict(beta, x)) for a, bb, x in segments(r)]
                out.append((float(r["outcome"] in sm.SUCCESS), pl, segs, r))
    return out


def main():
    from run_v03 import boot_diff
    from run_v04 import round_gauges, run
    rows = sm.load()
    D0.update(round_d0(rows))
    cards = list(csv.DictReader(open(HERE / "priors_v07.csv", encoding="utf-8")))

    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    v06 = run("priors_v06.csv", sm.DEEP_TWO_ON_ONE_KEEP_V04)
    sm.USE_FATIGUE = False
    global DEF_FAT_FROM_LABELS, USE_REATTACK
    v07 = lofo(rows, cards)
    USE_REATTACK = True
    v07_ra = lofo(rows, cards)
    beta_ra, cov_ra = fit_cov(rows, cards)
    DEF_FAT_FROM_LABELS = True
    v07_dl = lofo(rows, cards)
    beta_dl = fit(rows, cards)
    DEF_FAT_FROM_LABELS = USE_REATTACK = False
    base = sm.lofo_base(rows)
    print(f"{len(rows)} attempts, {len({r['fight_id'] for r in rows})} fights, leave-one-fight-out\n")
    print(f"{'model':46s} {'Brier@2s':>9s} {'Brier all-sec':>14s} {'logloss@2s':>11s}")
    for k, v in {"always the average": base, "v0.6": v06, "v0.7 (re-attack term off, recommended)": v07,
                 "v0.7 + re-attack term (card only)": v07_ra,
                 "v0.7 + re-attack term (card + labels)": v07_dl}.items():
        bl, bt, ll = sm.scores(v)
        print(f"{k:46s} {bl:9.3f} {bt:14.3f} {ll:11.3f}")
    for name, other in (("v0.6", v06), ("average", base)):
        m, ci = boot_diff(v07, other)
        print(f"v0.7 minus {name:7s}: {m:+.3f}  95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print("\nCalibration, v0.7, at the 2-s landmark:")
    for lo, hi, n, mp, ob in sm.calib(v07):
        a, bb = sm.wilson(round(ob * n), n)
        print(f"  {lo:.1f}-{min(hi, 1):.1f}  n={n:2d}  predicted {mp:.2f}  observed {ob:.2f}  [{a:.2f}, {bb:.2f}]")

    beta, cov = fit_cov(rows, cards)
    b0 = fit([], cards)
    print("\nWeights, all data: odds multiplier (80% range) [cards only]; def_fatigue from the re-attack-on fit {card + labels variant}")
    names = ["(real-world base, all zero)", "(sample oversampling)"] + FEATS
    for i, n_ in enumerate(names):
        if n_ == "def_fatigue":
            beta[i], cov[i, i] = beta_ra[i], cov_ra[i, i]
        se = math.sqrt(cov[i, i])
        print(f"  {n_:28s} x{math.exp(beta[i]):5.2f} ({math.exp(beta[i] - 1.2816 * se):5.2f}-{math.exp(beta[i] + 1.2816 * se):5.2f})"
              f"  [x{math.exp(b0[i]):5.2f}]" + (f"  {{x{math.exp(beta_dl[i]):.2f}}}" if n_ == "def_fatigue" else ""))

    print("\nRe-attack inputs (lingering fatigue at the start of each 2nd+ attempt):")
    for r in sorted(rows, key=key):
        d, n = D0[key(r)]
        if n > 1:
            print(f"  {r['attacker'][:16]:16s} R{r['round']} attempt {n}: D0 {d:4.2f} s -> def_fatigue {1 - math.exp(-d / DEF_FAT_SCALE):.2f}  ({r['outcome']})")

    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bc, cv = fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], cards)
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    tr = {round(t, 1): cc for t, cc, _, _ in round_gauges(rows)[id(r)][1]}
    print("\nPantoja vs Asakura R2 (fight left out), v0.7 on-screen values (real-world scale):")
    print(f"  {'t':>5s} {'finish':>7s} {'80% band':>10s} {'consc.':>7s}")
    for a, bb, x in segments(r):
        if abs(a - round(a)) < 1e-6 or abs(a - 6.6) < 1e-6 or abs(a - 14.9) < 1e-6:
            lo, hi = sm.interval(bc, cv, x)
            print(f"  {a:5.1f} {100 * sm.predict(bc, x, sample=False):6.0f}% {100 * lo:4.0f}-{100 * hi:3.0f}% {tr.get(round(a, 1), float('nan')):7.0f}")
    print(f"  {sm.duration(r):5.1f}   100%  (unconscious: event shown)")


if __name__ == "__main__":
    main()
