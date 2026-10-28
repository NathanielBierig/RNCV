"""Export the current finish model (v0.8) and the HP constants for the browser app (tools/app/model.json).

    python tools/app/export_model.py

Fitted on ALL labeled attempts (the app scores new clips, so no fight is held out). Derived numbers only: no footage.
Also writes a few reference states with Python's own finish % and squeeze, so the JavaScript port can be checked.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/model"))
import model_v07 as m  # noqa: E402
import run_v07_coach as rc  # noqa: E402
import state_model as sm  # noqa: E402


def main():
    rc.setup()                                     # v0.8: lean + coach priors
    rows = sm.load()
    m.D0.update(m.round_d0(rows))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    sm.USE_FATIGUE = False
    beta, _ = rc.fit_cov(rows, cards)
    mult = {f: float(__import__("math").exp(beta[2 + i])) for i, f in enumerate(m.FEATS)}
    refs = []
    for st in ({}, {"choke_arm_position": "under_chin", "rnc_style": "figure_four", "control": "body_triangle"},
               {"choke_arm_position": "over_jaw", "defender_two_on_one": "True", "chin_tucked": "True"},
               {"choke_arm_position": "under_chin", "rnc_style": "figure_four", "choking_hand_tucked": "True",
                "defender_two_on_one": "True", "opponent_flattened": "True"}):
        x = m.encode(st, 0.0, 0.0)
        refs.append({"state": st, "finish": sm.predict(beta, x, sample=False), "squeeze": sm.squeeze(sm.encode(st), sm.SQUEEZE_V06)})
    out = {
        "model": "v0.8", "n_attempts": len(rows), "n_fights": len({r["fight_id"] for r in rows}),
        "feats": m.FEATS, "beta": [float(b) for b in beta], "mult": mult,
        "unknown_grip": m.UNKNOWN_GRIP, "unknown_legs": m.UNKNOWN_LEGS, "other_locks": sorted(m.OTHER_LOCKS),
        "open_grips": sorted(sm.OPEN), "deep_keep": sm.DEEP_TWO_ON_ONE_KEEP, "fatigue_scale": sm.FATIGUE_SCALE,
        "squeeze": {k: v for k, v in sm.SQUEEZE_V06.items()}, "hp": {k: v for k, v in sm.CONSCIOUSNESS_V06.items()},
        "landmark": sm.LANDMARK, "refs": refs,
    }
    (Path(__file__).parent / "model.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("model", "n_attempts", "n_fights", "squeeze", "hp")}, indent=1))
    for r in refs:
        print(r)


if __name__ == "__main__":
    main()
