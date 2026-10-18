"""Leak-free fighter priors: one row per (fight_id, fighter), using only fights with
date < event_date (i.e. as of event_date - 1 day). The fight's own outcome never enters its row.

Output: fighter_priors.csv.  Run: .venv/Scripts/python -I build_fighter_priors.py
Shrinkage: rates are pulled toward the as-of global rate with K = 3 pseudo-fights (K0 = 3 pseudo
15-minute units for sub-attempt rates), so fighters with < 3 fights stay near the global mean.
`n_prior_fights` is exported so a model can see how much to trust a row.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import build_candidates as bc

HERE = Path(__file__).resolve().parent
K = 3.0
SUM_COLS = ["fight", "win", "sub_win", "rnc_win", "sub_loss", "rnc_loss",
            "stats_fight", "mins", "sub_att", "sub_att_faced"]


def build_rows():
    """Long table: one row per fighter appearance with this fight's own outcome columns."""
    res = bc.load_results()
    res = res[~res.bout_ambiguous & res.date.notna()].copy()
    st = pd.read_csv(bc.RAW / "ufc_fight_stats.csv").dropna(subset=["ROUND", "FIGHTER"])
    for c in ["EVENT", "BOUT", "FIGHTER"]:
        st[c] = bc.clean(st[c])
    st["sub_att"] = pd.to_numeric(st["SUB.ATT"], errors="coerce").fillna(0)
    per = st.groupby(["EVENT", "BOUT", "FIGHTER"], as_index=False)["sub_att"].sum()
    res["fight_min"] = ((res["round"] - 1) * 300 + res.finish_time_s) / 60.0
    rows = []
    for side, opp in [("fighter_1", "fighter_2"), ("fighter_2", "fighter_1")]:
        r = res[["fight_id", "EVENT", "BOUT", "date", "winner", "loser", "is_sub", "is_rnc", "finish_status",
                 "OUTCOME", "fight_min"]].copy()
        r["fighter"] = res[side]
        r["opponent"] = res[opp]
        rows.append(r)
    t = pd.concat(rows, ignore_index=True)
    t = t.merge(per.rename(columns={"FIGHTER": "fighter"}), left_on=["EVENT", "BOUT", "fighter"],
                right_on=["EVENT", "BOUT", "fighter"], how="left")
    opp_att = per.rename(columns={"FIGHTER": "opponent", "sub_att": "opp_sub_att"})
    t = t.merge(opp_att, on=["EVENT", "BOUT", "opponent"], how="left")
    valid = t.finish_status == "valid"
    t["fight"] = 1.0
    t["win"] = (t.fighter == t.winner).astype(float)
    t["sub_win"] = ((t.fighter == t.winner) & t.is_sub).astype(float)
    t["rnc_win"] = ((t.fighter == t.winner) & t.is_rnc & valid).astype(float)
    t["sub_loss"] = ((t.fighter == t.loser) & t.is_sub).astype(float)
    t["rnc_loss"] = ((t.fighter == t.loser) & t.is_rnc & valid).astype(float)
    has = t.sub_att.notna() & t.opp_sub_att.notna()
    t["stats_fight"] = has.astype(float)
    t["mins"] = np.where(has, t.fight_min, 0.0)
    t["sub_att"] = np.where(has, t.sub_att, 0.0)
    t["sub_att_faced"] = np.where(has, t.opp_sub_att, 0.0)
    return t


def _asof_sums(dates, vals, query_dates):
    """Sum of vals over entries with date < query date (strict), for sorted dates."""
    cum = np.vstack([np.zeros(vals.shape[1]), np.cumsum(vals, axis=0)])
    idx = np.searchsorted(dates, query_dates, side="left")
    return cum[idx], idx


def compute_priors(t):
    t = t.sort_values("date").reset_index(drop=True)
    dts = t.date.values.astype("datetime64[D]")
    # as-of global rates
    g, _ = _asof_sums(dts, t[SUM_COLS].to_numpy(float), dts)
    G = pd.DataFrame(g, columns=SUM_COLS)
    with np.errstate(divide="ignore", invalid="ignore"):
        g_sub_win = G.sub_win / G.fight
        g_sub_loss = G.sub_loss / G.fight
        g_rnc_win = G.rnc_win / G.fight
        g_att15 = G.sub_att / (G.mins / 15.0)
    out = t[["fight_id", "fighter", "opponent", "date"]].copy()
    P = np.zeros((len(t), len(SUM_COLS)))
    last = np.full(len(t), np.datetime64("NaT"), dtype="datetime64[D]")
    for _, grp in t.groupby("fighter", sort=False):
        ix = grp.index.to_numpy()
        d = dts[ix]
        s, idx = _asof_sums(d, t.loc[ix, SUM_COLS].to_numpy(float), d)
        P[ix] = s
        prev = np.where(idx > 0, d[np.maximum(idx - 1, 0)], np.datetime64("NaT"))
        last[ix] = prev
    Pf = pd.DataFrame(P, columns=SUM_COLS)
    out["n_prior_fights"] = Pf.fight
    out["n_prior_wins"] = Pf.win
    out["n_prior_sub_wins"] = Pf.sub_win
    out["n_prior_rnc_wins"] = Pf.rnc_win
    out["n_prior_sub_losses"] = Pf.sub_loss
    out["n_prior_rnc_losses"] = Pf.rnc_loss
    out["n_prior_fights_with_stats"] = Pf.stats_fight
    out["days_since_last_fight"] = (dts - last).astype("timedelta64[D]").astype(float)
    out["sub_win_rate_shrunk"] = (Pf.sub_win + K * g_sub_win) / (Pf.fight + K)
    out["rnc_win_rate_shrunk"] = (Pf.rnc_win + K * g_rnc_win) / (Pf.fight + K)
    out["sub_loss_rate_shrunk"] = (Pf.sub_loss + K * g_sub_loss) / (Pf.fight + K)
    out["sub_def_rate_shrunk"] = 1 - out.sub_loss_rate_shrunk
    out["sub_att_per15_shrunk"] = (Pf.sub_att + K * g_att15) / (Pf.mins / 15.0 + K)
    out["sub_att_faced_per15_shrunk"] = (Pf.sub_att_faced + K * g_att15) / (Pf.mins / 15.0 + K)
    out["prior_as_of"] = (pd.to_datetime(out.date) - pd.Timedelta(days=1)).dt.date
    out["date"] = pd.to_datetime(out.date).dt.date
    return out.sort_values(["date", "fight_id", "fighter"], ascending=[False, True, True])


if __name__ == "__main__":
    out = compute_priors(build_rows())
    out.to_csv(HERE / "fighter_priors.csv", index=False, float_format="%.5f")
    print(len(out), "rows;", out.fight_id.nunique(), "fights")
    print(out.n_prior_fights.describe().round(2).to_string())
