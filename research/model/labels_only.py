"""Labels-only estimates (no expert or coach priors) next to the model v0.8 multipliers.

    python research/model/labels_only.py      -> reports/labels_only.md

Firth logistic on all attempts with the details known at the 2-s landmark, one model with all details together,
95% profile intervals. Exploratory. This shows how much of each model v0.8 multiplier comes from the data itself
and how much from the priors. The pre-registered test (prereg_analysis.py) stays frozen.
"""
import math
import sys
from pathlib import Path

import numpy as np

import model_v07 as m
import run_v07_coach as rc
import state_model as sm
import csv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/rnc_science"))
import prereg_analysis as pa  # noqa: E402

SUCCESS = {"tap", "ref_stop", "unconscious"}
NAMES = ["Arm under the chin (vs over the jaw)", "Figure-four (vs one arm)", "Other lock (vs one arm)", "Body triangle (vs one hook / none)",
         "Both hooks (vs one hook / none)", "Defender two-on-one", "Choking hand hidden", "Defender flattened"]
FEAT = ["arm_under", "grip_f4", "grip_other", "legs_bt", "legs_hooks", "two_on_one", "hand_tucked", "flattened"]


def row(r):
    st = sm.state_at(r, sm.LANDMARK)
    arm = {"under_chin": 1.0, "over_jaw": 0.0}.get(st.get("choke_arm_position", ""))
    g, c = st.get("rnc_style", ""), st.get("control", "")
    f4, ot = (1.0, 0.0) if g == "figure_four" else (0.0, 1.0) if g in ("palm_to_palm", "gable", "wrist_pull") else (0.0, 0.0) if g in ("one_arm", "short_choke") else (None, None)
    bt, ho = (1.0, 0.0) if c == "body_triangle" else (0.0, 1.0) if c == "two_hooks" else (0.0, 0.0) if c in ("one_hook", "none") else (None, None)
    b = lambda k: {"True": 1.0, "False": 0.0}.get(st.get(k, ""))
    x = [1.0, arm, f4, ot, bt, ho, b("defender_two_on_one"), b("choking_hand_tucked"), b("opponent_flattened")]
    return None if None in x else x


def main():
    rows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"] and r["outcome"] != "bell"]
    pairs = [(row(r), r["outcome"] in SUCCESS) for r in rows if row(r)]
    X = np.array([x for x, _ in pairs]); y = np.array([v for _, v in pairs], float)
    beta, pl = pa.firth(X, y)
    rc.setup()
    mr = sm.load()
    m.D0.update(m.round_d0(mr))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.USE_FATIGUE = False
    bm, _ = rc.fit_cov(mr, cards)
    mult = {f: math.exp(bm[2 + i]) for i, f in enumerate(m.FEATS)}
    out = ["# Labels only vs model v0.8 (exploratory)", "",
           f"{len(y)} attempts with every detail known at the 2-s mark ({int(y.sum())} finishes). The labels-only column uses no expert or "
           "coach input. Where the two columns differ, the model's number leans on the priors. An interval that includes x1.0 means the "
           "labels alone can't yet tell whether the detail helps at all.", "",
           "| Detail (others held fixed) | Labels only (95% interval) | Model v0.8 (with priors) |", "|---|---|---|"]
    for j, (n, f) in enumerate(zip(NAMES, FEAT), start=1):
        lo, hi = pa.profile_ci(X, y, j, beta, pl)
        out.append(f"| {n} | x{math.exp(beta[j]):.2f} ({math.exp(lo):.2f}-{math.exp(hi):.2f}) | x{mult[f]:.2f} |")
    txt = "\n".join(out) + "\n"
    (ROOT / "reports/labels_only.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
