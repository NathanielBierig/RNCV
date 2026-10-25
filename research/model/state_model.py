"""RNCV finish model prototype (design A in docs/MODEL_SPEC.md): expert-prior Bayesian state model.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python -I research/model/state_model.py [--priors research/model/priors_placeholder.csv]

The number on screen = P(this attempt ends in a finish | the state right now, attempt still on).
  logit p = a + delta * selected_sample + sum_k b_k * x_k(state now)
- Expert priors enter as "prior data" (Greenland 2007; Bedrick, Christensen & Johnson 1996): each scenario card
  "state S finishes p% of the time" becomes n0 pseudo-attempts (p*n0 finishes, (1-p)*n0 non-finishes).
- Labels enter as one attempt = weight 1, split over its state segments by duration (G-panel state_changes),
  outcome = did the attempt end in a finish.
- delta absorbs the finish-list oversampling (cards are about the real-world rate, labels are not; PREREG §2).
  The overlay shows delta = 0; scoring on this sample uses delta.
- Weak ridge (sd 1.5 on log-odds) on every coefficient keeps it finite (Gelman et al. 2008-style).
Bell (1 attempt, 0.4 s) is left out: censored, as in PREREG §3.
"""
import argparse
import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SUCCESS = {"tap", "ref_stop", "unconscious"}
FEATS = ["arm_under", "grip_locked", "legs_strong", "two_on_one", "chin_tucked", "hand_tucked", "flattened", "fatigue"]
USE_FATIGUE = False      # attacker-fatigue term (MODEL_SPEC §2c); off = the v0.2 model exactly
FATIGUE_SCALE = 12.0     # fatigue = 1 - exp(-G / 12 s), G = seconds of squeeze effort so far: 0 at the start, ~0.4 after 6 s
GRID = 0.5               # time step for segments when fatigue is on (it changes continuously)
BUCKETS = {"<20": 0.10, "20-45": 0.325, "45-70": 0.575, ">70": 0.85}   # coarse-answer centers (MODEL_SPEC §3)
LOCKED = {"figure_four", "palm_to_palm", "gable", "wrist_pull"}
OPEN = {"one_arm", "short_choke"}
LANDMARK = 2.0


def load():
    rows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"] and r["sub_type"] == "rnc"]
    return [r for r in rows if r["outcome"] != "bell"]


def encode(st, fat=0.0):
    """State dict (+ attacker fatigue 0..1) -> feature vector. Unknown / unclear / blank = 0.5 (halfway)."""
    def b(v):
        return {"True": 1.0, "False": 0.0}.get(v, 0.5)
    arm = {"under_chin": 1.0, "over_jaw": 0.0}.get(st.get("choke_arm_position", ""), 0.5)
    g = st.get("rnc_style", "")
    grip = 1.0 if g in LOCKED else 0.0 if g in OPEN else 0.5
    c = st.get("control", "")
    legs = 1.0 if c in ("two_hooks", "body_triangle") else 0.0 if c in ("one_hook", "none") else 0.5
    return np.array([arm, grip, legs, b(st.get("defender_two_on_one", "")), b(st.get("chin_tucked", "")),
                     b(st.get("choking_hand_tucked", "")), b(st.get("opponent_flattened", "")), fat])


def changes(row):
    out = []
    for ch in filter(None, row.get("state_changes", "").split(">")):
        t, kv = ch.split(":", 1)
        k, v = kv.split("=", 1)
        out.append((float(t), k, v))
    return out


def state_at(row, t):
    st = {k: row.get(k, "") for k in ("choke_arm_position", "control", "defender_two_on_one", "chin_tucked",
                                      "choking_hand_tucked", "opponent_flattened")}
    st["rnc_style"] = row.get("rnc_style_at_L", "")
    for tc, k, v in changes(row):
        if tc <= t:
            st[k] = v
    return st


def duration(row):
    return float(row["video_time_end"]) - float(row["video_time_start"])


def segments(row):
    """[(t0, t1, x)] piecewise-constant state over the attempt (landmark values assumed from t = 0).
    With USE_FATIGUE, also cut every GRID seconds and carry the attacker's squeeze effort G (no recovery inside
    an attempt: he's squeezing the whole time)."""
    dur = duration(row)
    cuts = {0.0, dur, *[t for t, _, _ in changes(row) if 0 < t < dur]}
    if USE_FATIGUE:
        cuts |= set(np.arange(GRID, dur, GRID).round(3))
    cuts = sorted(cuts)
    out, G = [], 0.0
    for a, b in zip(cuts, cuts[1:]):
        if b <= a:
            continue
        st = state_at(row, a)
        fat = 1 - math.exp(-G / FATIGUE_SCALE) if USE_FATIGUE else 0.0
        x = encode(st, fat)
        out.append((a, b, x))
        G += (b - a) * squeeze(x)
    return out


def x_at(row, t):
    """Feature vector at time t into the attempt (the segment containing t)."""
    segs = segments(row)
    return next((x for a, b, x in segs if a <= t < b), segs[-1][2])


def selected(row):
    return 0.0 if row["found_via"] == "random_fight" else 1.0


def card_p(c):
    """A card's finish chance: the owner's % (p_finish), or the center of a coarse bucket (<20, 20-45, 45-70, >70)."""
    return BUCKETS[c["bucket"]] if c.get("bucket") else float(c["p_finish"])


def card_weight(c):
    """Pretend-attempt count of a card. If the owner gave a range (p_low, p_high, read as a 90% range), use the
    Beta distribution with that mean and spread: n0 = p(1-p)/sd^2 - 1, sd = (high-low)/3.29, kept to 1..10.
    Otherwise the n0 column (default 4). Capped at 10 so no single card outweighs ten real attempts.
    A bucket answer ("I'm not sure, somewhere 20-45%") gets 3 attempts' worth (n0 column overrides), so labels win there."""
    if c.get("bucket"):
        return float(c.get("n0") or 3)
    if c.get("p_low") and c.get("p_high"):
        p, sd = float(c["p_finish"]), (float(c["p_high"]) - float(c["p_low"])) / 3.29
        return float(np.clip(p * (1 - p) / max(sd, 1e-3) ** 2 - 1, 1, 10))   # cap 10: experts give ranges that are too narrow (O'Hagan et al. 2006)
    return float(c.get("n0") or 4)


def design(rows, cards, n0_scale=1.0):
    """Stack weighted rows: columns = [1, selected, FEATS...]."""
    X, y, w = [], [], []
    for r in rows:
        dur, yy = duration(r), float(r["outcome"] in SUCCESS)
        for a, b, x in segments(r):
            X.append(np.r_[1.0, selected(r), x]); y.append(yy); w.append((b - a) / dur)
    for c in cards:
        if not USE_FATIGUE and float(c.get("fatigue") or 0):
            continue                                         # fatigue cards only make sense with the fatigue term on
        x = np.r_[1.0, 0.0, [float(c.get(f) or 0) for f in FEATS]]
        n0, pc = card_weight(c) * n0_scale, card_p(c)
        for yy, ww in ((1.0, pc * n0), (0.0, (1 - pc) * n0)):
            if ww > 0:
                X.append(x); y.append(yy); w.append(ww)
    return np.array(X), np.array(y), np.array(w)


def fit(rows, cards, n0_scale=1.0, ridge_sd=1.5, use_delta=True):
    X, y, w = design(rows, cards, n0_scale)
    if not use_delta:
        X[:, 1] = 0.0
    P = np.full(X.shape[1], 1 / ridge_sd ** 2)
    P[0] = 1 / 10 ** 2                                       # intercept: nearly flat
    beta = np.zeros(X.shape[1])
    for _ in range(100):                                     # Newton-Raphson, penalized weighted logistic
        p = 1 / (1 + np.exp(-X @ beta))
        g = X.T @ (w * (y - p)) - P * beta
        Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P)
        step = np.linalg.solve(Hm, g)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def fit_cov(rows, cards, n0_scale=1.0, ridge_sd=1.5):
    """MAP coefficients + Laplace covariance (inverse penalized Hessian) for honest uncertainty bands."""
    beta = fit(rows, cards, n0_scale, ridge_sd)
    X, y, w = design(rows, cards, n0_scale)
    P = np.full(X.shape[1], 1 / ridge_sd ** 2)
    P[0] = 1 / 10 ** 2
    p = 1 / (1 + np.exp(-X @ beta))
    Hm = (X * (w * p * (1 - p))[:, None]).T @ X + np.diag(P)
    return beta, np.linalg.inv(Hm)


def interval(beta, cov, x, sample=False, z=1.2816):
    """80% band on the probability scale (delta method on the log-odds)."""
    v = np.r_[1.0, 1.0 if sample else 0.0, x]
    zc, se = v @ beta, math.sqrt(v @ cov @ v)
    f = lambda q: 1 / (1 + math.exp(-q))
    return f(zc - z * se), f(zc + z * se)


# ---- defender gauge ("air"): squeeze exposure, a leaky integrator over the visible state ----
GAUGE = {"secs_to_out": 9.0, "recovery_secs": 8.0, "leak_below": 0.3}   # placeholders: owner Q-G1 / Q-G2
# secs_to_out ~9 s: full carotid occlusion causes unconsciousness in ~6-7 s (Rossen, Kabat & Anderson 1943);
# fight chokes are rarely full, so a little longer. Not tuned on any clip.


def squeeze(x):
    """How hard the visible state squeezes, 0..1 (placeholder weights; owner cards Q-G3).
    Under chin + locked = 1; over the jaw ~0.15; a two-on-one or a tucked chin takes some of it away."""
    arm, grip, legs, two, chin, hand, flat = x[:7]
    base = arm * (0.45 + 0.55 * grip) + (1 - arm) * 0.15
    return float(np.clip(base * (1 - 0.35 * two) * (1 - 0.3 * chin) * (1 + 0.15 * hand), 0, 1))


def health_trace(row, dt=0.1, g=GAUGE):
    """Defender health 100 -> 0: E grows at squeeze(state) per second; it recovers (E / recovery_secs per second)
    only while the squeeze is light (< leak_below), i.e. once the defender gets blood flowing again."""
    E, out, t, dur = 0.0, [], 0.0, duration(row)
    while t <= dur + 1e-9:
        s_ = squeeze(encode(state_at(row, t)))
        E = max(0.0, E + dt * (s_ - (E / g["recovery_secs"] if s_ < g["leak_below"] else 0.0)))
        out.append((t, 100 * max(0.0, 1 - E / g["secs_to_out"])))
        t += dt
    return out


def predict(beta, x, sample=True):
    z = beta[0] + (beta[1] if sample else 0.0) + x @ beta[2:]
    return 1 / (1 + math.exp(-z))


def lofo(rows, cards, **kw):
    """Leave-one-fight-out predictions: per attempt, (y, p at landmark, [(weight, p) over segments])."""
    out = []
    for fid in sorted({r["fight_id"] for r in rows}):
        beta = fit([r for r in rows if r["fight_id"] != fid], cards, **kw)
        for r in rows:
            if r["fight_id"] == fid:
                dur = duration(r)
                pl = predict(beta, x_at(r, min(LANDMARK, dur)))
                segs = [((b - a) / dur, predict(beta, x)) for a, b, x in segments(r)]
                out.append((float(r["outcome"] in SUCCESS), pl, segs, r))
    return out


def lofo_base(rows):
    out = []
    for r in rows:
        tr = [q for q in rows if q["fight_id"] != r["fight_id"]]
        p = (sum(q["outcome"] in SUCCESS for q in tr) + 1) / (len(tr) + 2)
        out.append((float(r["outcome"] in SUCCESS), p, [(1.0, p)], r))
    return out


def lofo_mvp01(rows):
    """The rejected MVP 0.1 value (state p x time ramp, EMA-smoothed) at the landmark and over the attempt."""
    import sys
    sys.path.insert(0, str(ROOT / "tools/mvp"))
    import demo
    allrows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")) if "excluded_" not in r["notes"]]
    out = []
    for r in rows:
        m = demo.fit([q for q in allrows if q["fight_id"] != r["fight_id"]])
        dur, shown, trace = duration(r), 0.0, []
        for i in range(int(dur * 30) + 1):
            el = i / 30
            p = demo.finish_prob(m, demo.state_at(r, el)) if el >= 2 else m["base"]
            shown += (p * (1 - math.exp(-el / max(m["tau"], 1))) - shown) * 0.15
            trace.append(shown)
        out.append((float(r["outcome"] in SUCCESS), trace[min(60, len(trace) - 1)], [(1 / len(trace), v) for v in trace], r))
    return out


def scores(preds):
    y = np.array([a for a, _, _, _ in preds])
    pl = np.clip(np.array([b for _, b, _, _ in preds]), 1e-4, 1 - 1e-4)
    brier_l = float(np.mean((pl - y) ** 2))
    brier_t = float(np.mean([sum(w * (p - yy) ** 2 for w, p in s) for yy, _, s, _ in preds]))
    ll = float(-np.mean(y * np.log(pl) + (1 - y) * np.log(1 - pl)))
    return brier_l, brier_t, ll


def calib(preds, edges=(0, .2, .4, .6, .8, 1.0001), timeweighted=False):
    lines = []
    for lo, hi in zip(edges, edges[1:]):
        if timeweighted:
            pts = [(w, p, yy) for yy, _, s, _ in preds for w, p in s if lo <= p < hi]
            n = sum(w for w, _, _ in pts)
            if n:
                lines.append((lo, hi, n, sum(w * p for w, p, _ in pts) / n, sum(w * yy for w, _, yy in pts) / n))
        else:
            pts = [(p, yy) for yy, p, _, _ in preds if lo <= p < hi]
            if pts:
                lines.append((lo, hi, len(pts), np.mean([p for p, _ in pts]), np.mean([yy for _, yy in pts])))
    return lines


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 1)
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--priors", default=str(ROOT / "research/model/priors_placeholder.csv"))
    a = ap.parse_args()
    rows = load()
    cards = list(csv.DictReader(open(a.priors, encoding="utf-8")))
    y = [r["outcome"] in SUCCESS for r in rows]
    print(f"attempts {len(rows)} (bell excluded) from {len({r['fight_id'] for r in rows})} fights; finishes {sum(y)}")
    print(f"found_via: {sorted({r['found_via'] for r in rows})}  (no random_fight rows yet -> real-world base rate = owner's prior only)\n")

    runs = {"M0 base rate only": lofo_base(rows),
            "M1 MVP 0.1 (rejected)": lofo_mvp01(rows),
            "M2 labels only (no priors)": lofo(rows, [], ridge_sd=1.5),
            "M3 priors only (cards, no labels)": [(yy, predict(fit([], cards), encode(state_at(r, min(LANDMARK, duration(r))))),
                                                   [((b - s) / duration(r), predict(fit([], cards), x)) for s, b, x in segments(r)], r)
                                                  for yy, _, _, r in lofo_base(rows)],
            }
    for sc in (0.5, 1.0, 2.0):
        runs[f"M4 priors + labels (n0 x{sc:g})"] = lofo(rows, cards, n0_scale=sc)
    global USE_FATIGUE
    USE_FATIGUE = True
    runs["M5 = M4 + attacker fatigue"] = lofo(rows, cards)
    beta_f = fit(rows, cards)
    r_pa = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    b_pa = fit([q for q in rows if q["fight_id"] != r_pa["fight_id"]], cards)
    trace_f = [(s_, predict(b_pa, x, sample=False)) for s_, _, x in segments(r_pa)]
    USE_FATIGUE = False
    bucket_cards = [dict(c, bucket=min(BUCKETS, key=lambda k: abs(BUCKETS[k] - float(c["p_finish"]))), n0="") for c in cards]
    runs["M6 = M4 with bucket answers (3 each)"] = lofo(rows, bucket_cards)
    print("Leave-one-fight-out scores (lower = better; Brier 0.25 = coin flip at 50%):")
    print(f"{'model':38s} {'Brier@2s':>9s} {'Brier time-avg':>15s} {'logloss@2s':>11s}")
    base_bl = scores(runs["M0 base rate only"])[0]
    for k, v in runs.items():
        bl, bt, ll = scores(v)
        print(f"{k:38s} {bl:9.3f} {bt:15.3f} {ll:11.3f}")
    print(f"(M3 uses no labels, so it isn't leave-one-out; its sample-scale intercept is the owner's real-world one, which is why it under-predicts on this finish-heavy sample)\n")

    best = runs["M4 priors + labels (n0 x1)"]
    for tw in (False, True):
        print("Calibration, M4 n0 x1, " + ("time-weighted over every second of every attempt" if tw else "at the 2-s landmark (one row per attempt)"))
        print(f"  {'bin':10s} {'n':>5s} {'mean pred':>10s} {'observed':>9s}  95% CI (Wilson, landmark only)")
        for lo, hi, n, mp, ob in calib(best, timeweighted=tw):
            ci = wilson(round(ob * n), round(n)) if not tw else None
            cis = f"  [{ci[0]:.2f}, {ci[1]:.2f}]" if ci else ""
            print(f"  {lo:.1f}-{min(hi, 1):.1f}  {n:5.1f} {mp:10.2f} {ob:9.2f}{cis}")
        print()

    beta = fit(rows, cards)
    print("M4 fit on all 35 attempts (log-odds; exp = odds ratio). Prior-only fit in brackets:")
    b0 = fit([], cards)
    for name, v, v0 in zip(["intercept (world)", "delta (sample oversampling)"] + FEATS, beta, b0):
        print(f"  {name:28s} {v:+.2f}  OR {math.exp(v):5.2f}   [{v0:+.2f}]")

    print("\nPantoja vs Asakura R2 (fight left out), what M4 would show on screen (real-world scale, delta = 0):")
    r = next(q for q in rows if q["video_url"].startswith("pantoja_asakura"))
    bl = fit([q for q in rows if q["fight_id"] != r["fight_id"]], cards)
    for s, e, x in segments(r):
        print(f"  {s:5.1f}-{e:5.1f}s  {dict(zip(FEATS, x))}  ->  {100 * predict(bl, x, sample=False):4.0f}%  (sample scale {100 * predict(bl, x):.0f}%)")
    print(f"  {duration(r):5.1f}s  outcome observed: {r['outcome']}  ->  100% (event shown, not predicted)")
    bc, cov = fit_cov([q for q in rows if q["fight_id"] != r["fight_id"]], cards)
    print("  80% bands (real-world scale):", [f"{100 * lo:.0f}-{100 * hi:.0f}%" for lo, hi in (interval(bc, cov, x) for _, _, x in segments(r))])
    print("  defender health:", " ".join(f"{t:.0f}s:{h:.0f}" for t, h in health_trace(r)[::20]), f"end:{health_trace(r)[-1][1]:.0f}")

    print(f"\nAttacker fatigue term (M5, all data): log-odds {beta_f[-1]:+.2f} at full fatigue (OR {math.exp(beta_f[-1]):.2f})")
    print("  Pantoja with fatigue:", " ".join(f"{t_:.1f}s:{100 * p_:.0f}%" for t_, p_ in trace_f[::4]), f"last:{100 * trace_f[-1][1]:.0f}%")

    print("\nDefender gauge check (no fitting; placeholder weights): health at the end, finishes vs not")
    fin = [health_trace(q)[-1][1] for q in rows if q["outcome"] in SUCCESS]
    non = [health_trace(q)[-1][1] for q in rows if q["outcome"] not in SUCCESS]
    auc = np.mean([(a < b) + 0.5 * (a == b) for a in fin for b in non])
    print(f"  median end health: finishes {np.median(fin):.0f}, not {np.median(non):.0f};  AUC (lower health = finish) {auc:.2f}")
    print(f"  finishes ending with health <= 20: {sum(h <= 20 for h in fin)}/{len(fin)};  non-finishes: {sum(h <= 20 for h in non)}/{len(non)}")


if __name__ == "__main__":
    main()
