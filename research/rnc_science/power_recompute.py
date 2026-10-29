"""Honest sample-size recompute for the pre-registered test (dated note, 2026-10-29; the frozen plan is unchanged).

    python research/rnc_science/power_recompute.py      -> research/rnc_science/power_recompute_output.txt

PREREG §8's "about 150" assumed two balanced groups of ~75. The real groups are unbalanced (pilot labels: arm under
the chin 78%, strong legs 70%, defender two-on-one 32%), which costs power. This simulates the exact pre-registered
analysis (prereg_analysis.py: Firth logistic, profile 95% CIs, verdict rule) on fake datasets with those proportions
and two effect scenarios, and reports the share of runs where each hypothesis comes out SUPPORTED (= power).
  A "coach view"  : H1 x4, H2 x2, H3 x0.3   (what the pre-registration expected)
  B "pilot view"  : H1 x4.6, H2 x1.0, H3 x0.56 (model v0.8 adjusted estimates, 71 attempts)
"""
import math

import numpy as np

import prereg_analysis as pa

P_ARM, P_LEGS, P_TWO = 0.78, 0.70, 0.32
SCEN = {"A coach view (x4, x2, x0.3)": (math.log(4), math.log(2), math.log(0.3)),
        "B pilot view (x4.6, x1.0, x0.56)": (math.log(4.6), 0.0, math.log(0.56))}
NS, SIMS = (100, 150, 200, 300), 60


def simulate(n, eff, seed):
    rng = np.random.default_rng(seed)
    b1, b2, b3 = eff
    rows = []
    for _ in range(n):
        arm, legs, two = rng.random() < P_ARM, rng.random() < P_LEGS, rng.random() < P_TWO
        start = rng.uniform(0, 280)
        eta = -0.9 + b1 * arm + b2 * legs + b3 * two + 0.05 * (300 - start) / 60
        ok = rng.random() < 1 / (1 + math.exp(-eta))
        rows.append({"choke_arm_position": "under_chin" if arm else "over_jaw",
                     "control": "body_triangle" if legs else "one_hook", "defender_two_on_one": str(two),
                     "attempt_start_s": f"{start:.1f}", "attempt_end_s": f"{start + 10:.1f}",
                     "outcome": "tap" if ok else "escape", "success": str(ok), "rnc_style_at_L": "figure_four",
                     "notes": "", "camera_cut_flag": "none", "found_via": "finish_list", "attacker": f"A{rng.integers(60)}"})
    return rows


def main():
    print(f"group shares: arm under the chin {P_ARM:.0%}, strong legs {P_LEGS:.0%}, two-on-one {P_TWO:.0%}; "
          f"{SIMS} simulated studies per cell\n")
    for name, eff in SCEN.items():
        print(name)
        print(f"  {'n':>5s} {'H1 supported':>13s} {'H2 supported':>13s} {'H3 supported':>13s}")
        for n in NS:
            sup = np.zeros(3)
            for s in range(SIMS):
                X, y, _ = pa.design(simulate(n, eff, 1000 * n + s))
                res, _ = pa.fit_report(X, y)
                for j in range(3):
                    _, b, lo, hi = res[j]
                    sup[j] += pa.verdict(j + 1, lo, hi) == "SUPPORTED"
            print(f"  {n:5d} {sup[0] / SIMS:13.0%} {sup[1] / SIMS:13.0%} {sup[2] / SIMS:13.0%}", flush=True)
        print()


if __name__ == "__main__":
    main()
