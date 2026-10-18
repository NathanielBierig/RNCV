"""Leak test: a fight's own prior row must not depend on its own outcome or on any later fight.
Run: .venv/Scripts/python -I test_priors_leak.py   (exit 0 = pass)"""
import sys
import numpy as np
import pandas as pd
import build_fighter_priors as bp

t = bp.build_rows()
base = bp.compute_priors(t).set_index(["fight_id", "fighter"])
rng = np.random.default_rng(0)
fids = rng.choice(t.fight_id.unique(), 12, replace=False)
num = [c for c in base.columns if base[c].dtype.kind == "f"]
bad = 0
for fid in fids:
    d = t[t.fight_id == fid].date.iloc[0]
    # (b) corrupt this fight's own outcome columns, keep everything else
    t2 = t.copy()
    m = t2.fight_id == fid
    for c in ["win", "sub_win", "rnc_win", "sub_loss", "rnc_loss", "sub_att", "sub_att_faced", "mins"]:
        t2.loc[m, c] = t2.loc[m, c] + 7
    # (c) drop all later fights
    t3 = t[(t.date <= d)]
    for name, tt in [("own-outcome-changed", t2), ("later-fights-removed", t3)]:
        new = bp.compute_priors(tt).set_index(["fight_id", "fighter"])
        for key in base.loc[fid].index.map(lambda f: (fid, f)):
            a, b = base.loc[key, num], new.loc[key, num]
            if not np.allclose(a.fillna(-1).to_numpy(float), b.fillna(-1).to_numpy(float), atol=1e-9):
                bad += 1
                print("LEAK", name, key)
print("checked", len(fids), "fights;", "failures:", bad)
sys.exit(1 if bad else 0)
