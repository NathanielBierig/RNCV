"""Pre-registered primary analysis (PREREG.md §5, §7, §8), written before the data are complete.

    python research/rnc_science/prereg_analysis.py            # self-test on SIMULATED data (default)
    python research/rnc_science/prereg_analysis.py --real     # the real run: only at the PREREG target (~150 attempts)

Primary model: Firth logistic regression, success ~ H1 arm under the chin + H2 strong legs (body triangle or
two hooks) + H3 defender two-on-one + round time left (adjustment only), all coded at the landmark L = 2 s.
Profile-likelihood 95% CIs, reported as odds ratios, and the §8 verdict per hypothesis
(supported / contradicted / inconclusive).
Exclusions (§3, §4): bell (censored), one-armed chokes (rnc_style_at_L = one_arm), attempts shorter than
L + 2 s = 4 s, rows tagged excluded_ in notes. `unclear` / blank factors = missing (complete case).
Sensitivity (§7): (a) cluster bootstrap by attacker; (b) unclear coded as each extreme; (c) without cut_out rows.

OPEN POINT for the owner, to settle BEFORE --real: PREREG §2 says the analysis "adjusts for found_via", while §5
caps the primary model at 4 df. Default here: found_via is NOT in the primary model and enters sensitivity (d)
(primary + a selected-vs-random indicator). Flip ADJUST_FOUND_VIA if the owner reads it the other way.
"""
import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize

ROOT = Path(__file__).resolve().parents[2]
ADJUST_FOUND_VIA = False
L, MIN_DUR = 2.0, 4.0
NAMES = ["intercept", "H1 arm under the chin", "H2 strong legs", "H3 defender two-on-one", "round time left (per min)"]
PRED = {1: +1, 2: +1, 3: -1}                      # predicted direction of H1-H3


# ---------------- Firth logistic regression ----------------
def pen_loglik(beta, X, y):
    eta = X @ beta
    p = 1 / (1 + np.exp(-eta))
    ll = np.sum(y * eta - np.logaddexp(0, eta))
    W = p * (1 - p)
    sign, logdet = np.linalg.slogdet((X * W[:, None]).T @ X)
    return ll + 0.5 * logdet


def firth(X, y, fixed=None):
    """Maximize the Firth-penalized log-likelihood; fixed = (j, value) holds one coefficient (profile)."""
    k = X.shape[1]
    free = [i for i in range(k) if fixed is None or i != fixed[0]]

    def full(b):
        beta = np.zeros(k)
        beta[free] = b
        if fixed is not None:
            beta[fixed[0]] = fixed[1]
        return beta

    res = minimize(lambda b: -pen_loglik(full(b), X, y), np.zeros(len(free)), method="BFGS",
                   options={"gtol": 1e-8, "maxiter": 2000})
    return full(res.x), -res.fun


def profile_ci(X, y, j, beta, pl_max, level=0.95):
    crit = 3.841458820694124 if level == 0.95 else None
    f = lambda b: 2 * (pl_max - firth(X, y, (j, b))[1]) - crit
    out = []
    for direction in (-1, 1):
        step, b = 0.5, beta[j]
        while f(b + direction * step) < 0 and step < 40:
            step *= 2
        out.append(brentq(f, b, b + direction * step, xtol=1e-6) if step < 40 else direction * math.inf)
    return out


def fit_report(X, y, boot_groups=None, n_boot=0, seed=0):
    beta, pl = firth(X, y)
    rows = []
    for j in range(1, X.shape[1]):
        lo, hi = profile_ci(X, y, j, beta, pl)
        rows.append((NAMES[j] if j < len(NAMES) else f"x{j}", beta[j], lo, hi))
    boot = None
    if n_boot and boot_groups is not None:
        rng = np.random.default_rng(seed)
        groups = np.unique(boot_groups)
        bs = []
        for _ in range(n_boot):
            pick = rng.choice(groups, len(groups))
            idx = np.concatenate([np.where(boot_groups == g)[0] for g in pick])
            bs.append(firth(X[idx], y[idx])[0])
        bs = np.array(bs)
        boot = np.percentile(bs, [2.5, 97.5], axis=0)
    return rows, boot


def verdict(j, lo, hi):
    if j not in PRED:
        return "adjustment"
    d = PRED[j]
    if (d > 0 and lo > 0) or (d < 0 and hi < 0):
        return "SUPPORTED"
    if (d > 0 and hi < 0) or (d < 0 and lo > 0):
        return "CONTRADICTED"
    return "inconclusive"


# ---------------- data ----------------
def code(r, unclear_as=None):
    """Return the covariate row or None (excluded / missing). unclear_as: None, 0 or 1 (sensitivity b)."""
    def val(v, yes, no):
        if v in yes:
            return 1.0
        if v in no:
            return 0.0
        return unclear_as
    arm = val(r["choke_arm_position"], {"under_chin"}, {"over_jaw"})
    legs = val(r["control"], {"body_triangle", "two_hooks"}, {"one_hook", "none"})
    two = val(r["defender_two_on_one"], {"True"}, {"False"})
    left = (300.0 - float(r["attempt_start_s"])) / 60.0
    x = [1.0, arm, legs, two, left]
    if ADJUST_FOUND_VIA:
        x.append(0.0 if r["found_via"] == "random_fight" else 1.0)
    return None if any(v is None for v in x) else x


def eligible(r):
    dur = float(r["attempt_end_s"]) - float(r["attempt_start_s"])
    return (r["outcome"] != "bell" and r["rnc_style_at_L"] != "one_arm" and dur >= MIN_DUR
            and "excluded_" not in r["notes"])


def design(rows, unclear_as=None, drop_cut_out=False):
    X, y, g = [], [], []
    for r in rows:
        if not eligible(r) or (drop_cut_out and r["camera_cut_flag"] == "cut_out"):
            continue
        x = code(r, unclear_as)
        if x is not None:
            X.append(x); y.append(float(r["success"] == "True")); g.append(r["attacker"])
    return np.array(X), np.array(y), np.array(g)


def report(rows, n_boot=500):
    out = []
    X, y, g = design(rows)
    res, boot = fit_report(X, y, g, n_boot)
    out += [f"Primary model: n = {len(y)} attempts, {int(y.sum())} finishes, {len(np.unique(g))} attackers.", "",
            "| Term | Odds ratio | 95% profile CI | Cluster bootstrap 95% (by attacker) | Verdict (§8) |", "|---|---|---|---|---|"]
    for j, (n, b, lo, hi) in enumerate(res, start=1):
        bt = f"{math.exp(boot[0][j]):.2f}–{math.exp(boot[1][j]):.2f}" if boot is not None else "—"
        out.append(f"| {n} | {math.exp(b):.2f} | {math.exp(lo):.2f}–{math.exp(hi):.2f} | {bt} | {verdict(j, lo, hi)} |")
    for label, kw in (("(b) unclear = 0", {"unclear_as": 0.0}), ("(b) unclear = 1", {"unclear_as": 1.0}),
                      ("(c) without cut_out", {"drop_cut_out": True})):
        Xs, ys, _ = design(rows, **kw)
        r2, _ = fit_report(Xs, ys)
        out.append(f"\nSensitivity {label} (n = {len(ys)}): " + "; ".join(
            f"{n.split(' ')[0]} OR {math.exp(b):.2f} [{math.exp(lo):.2f}, {math.exp(hi):.2f}] {verdict(j, lo, hi)}"
            for j, (n, b, lo, hi) in enumerate(r2[:3], start=1)))
    return "\n".join(out)


# ---------------- self-test ----------------
def simulate(n=150, seed=1, true=(-1.0, 1.4, 0.7, -1.2, 0.1)):
    """Fake attempts with KNOWN odds ratios (H1 x4.1, H2 x2.0, H3 x0.30), to check the code recovers them."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        arm, legs, two = rng.random() < 0.55, rng.random() < 0.6, rng.random() < 0.4
        start = rng.uniform(0, 280)
        eta = true[0] + true[1] * arm + true[2] * legs + true[3] * two + true[4] * (300 - start) / 60
        ok = rng.random() < 1 / (1 + math.exp(-eta))
        rows.append({"choke_arm_position": "under_chin" if arm else "over_jaw",
                     "control": rng.choice(["body_triangle", "two_hooks"]) if legs else rng.choice(["one_hook", "none"]),
                     "defender_two_on_one": str(two), "attempt_start_s": f"{start:.1f}",
                     "attempt_end_s": f"{start + rng.uniform(4, 30):.1f}", "outcome": "tap" if ok else "escape",
                     "success": str(ok), "rnc_style_at_L": "figure_four", "notes": "", "camera_cut_flag": "none",
                     "found_via": "finish_list", "attacker": f"A{rng.integers(40)}"})
    return rows


def main():
    if "--real" in sys.argv:
        rows = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
        if len(rows) < 150 and "--force" not in sys.argv:
            raise SystemExit(f"only {len(rows)} attempts; PREREG target is ~150. Not running the confirmatory "
                             "analysis early (add --force only if the owner decides to stop labeling).")
        txt = report(rows)
        (ROOT / "reports/prereg_analysis.md").write_text("# Pre-registered primary analysis\n\n" + txt + "\n", encoding="utf-8")
        print(txt)
        return
    print("SELF-TEST on simulated data (true odds ratios: H1 x4.06, H2 x2.01, H3 x0.30, time x1.11/min)\n")
    print(report(simulate(), n_boot=100))


if __name__ == "__main__":
    main()
