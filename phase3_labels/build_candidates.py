"""Build RNC success list + failed-attempt candidate list from ufcstats-derived CSVs.

Input : raw_sources/*.csv (Greco1899/scrape_ufc_stats snapshot, GPL-3.0, data scraped from ufcstats.com)
Output: rnc_successes.csv, failed_attempt_candidates.csv, summary_stats.json
Run   : .venv/Scripts/python -I build_candidates.py
"""
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw_sources"


def clean(s):
    return s.fillna("").astype(str).str.strip()


def fight_id(url):
    return url.rstrip("/").split("/")[-1]


def mmss(t):
    m, s = str(t).strip().split(":")
    return int(m) * 60 + int(s)


events = pd.read_csv(RAW / "ufc_event_details.csv")
events["EVENT"] = clean(events["EVENT"])
events["date"] = pd.to_datetime(events["DATE"].str.strip(), format="%B %d, %Y").dt.date
res = pd.read_csv(RAW / "ufc_fight_results.csv")
for c in ["EVENT", "BOUT", "METHOD", "DETAILS", "WEIGHTCLASS"]:
    res[c] = clean(res[c])
res["fight_id"] = res["URL"].map(fight_id)
res = res.merge(events[["EVENT", "date", "URL"]].rename(columns={"URL": "event_url"}), on="EVENT", how="left")
res["fighter_1"] = res["BOUT"].str.split(" vs\\. ", n=1, regex=True).str[0].str.strip()
res["fighter_2"] = res["BOUT"].str.split(" vs\\. ", n=1, regex=True).str[1].str.strip()
res["winner"] = None
res.loc[res.OUTCOME == "W/L", "winner"] = res["fighter_1"]
res.loc[res.OUTCOME == "L/W", "winner"] = res["fighter_2"]
res["loser"] = None
res.loc[res.OUTCOME == "W/L", "loser"] = res["fighter_2"]
res.loc[res.OUTCOME == "L/W", "loser"] = res["fighter_1"]
res["round"] = pd.to_numeric(res["ROUND"], errors="coerce")
res["finish_time_s"] = res["TIME"].map(mmss)
res["is_sub"] = res.METHOD == "Submission"
res["is_rnc"] = res.is_sub & res.DETAILS.str.startswith("Rear Naked Choke")
res["rnc_variant"] = res.DETAILS.map(
    lambda d: "technical_submission" if "Technical" in d else "standard"
)

# ---- 1. RNC successes -------------------------------------------------------
rnc = res[res.is_rnc].copy()
succ = pd.DataFrame(
    {
        "fight_id": rnc.fight_id,
        "event": rnc.EVENT,
        "date": rnc.date,
        "fighter_1": rnc.fighter_1,
        "fighter_2": rnc.fighter_2,
        "winner_attacker": rnc.winner,
        "defender": rnc.loser,
        "round": rnc["round"].astype("Int64"),
        "finish_time_in_round": rnc.TIME.str.strip(),
        "finish_time_in_round_s": rnc.finish_time_s,
        "weight_class": rnc.WEIGHTCLASS,
        "rnc_variant": rnc.rnc_variant,
        "ufcstats_url": rnc.URL,
    }
).sort_values("date", ascending=False)
succ.to_csv(HERE / "rnc_successes.csv", index=False)

# ---- 2. failed-attempt candidates (per round) -------------------------------
st = pd.read_csv(RAW / "ufc_fight_stats.csv")
for c in ["EVENT", "BOUT", "FIGHTER"]:
    st[c] = clean(st[c])
st = st.dropna(subset=["ROUND", "FIGHTER"]).copy()
st["round"] = st["ROUND"].str.extract(r"(\d+)").astype(int)
st["sub_att"] = pd.to_numeric(st["SUB.ATT"], errors="coerce").fillna(0).astype(int)
st = st.merge(
    res[["EVENT", "BOUT", "fight_id", "date", "winner", "is_sub", "round", "METHOD", "DETAILS", "WEIGHTCLASS", "URL"]]
    .rename(columns={"round": "finish_round"}),
    on=["EVENT", "BOUT"],
    how="left",
)
unmatched = st.fight_id.isna().sum()
st = st[st.sub_att > 0].copy()
# round ended in a submission = the fight's finishing round, when the finish was a submission
st["round_ended_in_sub"] = st.is_sub & (st["round"] == st.finish_round)
cand = st[~st.round_ended_in_sub].copy()
# defender = other fighter of the bout
def other(row):
    f = [x.strip() for x in row.BOUT.split(" vs. ", 1)]
    return f[1] if row.FIGHTER == f[0] else f[0]

cand["defender"] = cand.apply(other, axis=1)
cand["fight_result_method"] = cand.METHOD.fillna("") + cand.DETAILS.fillna("").where(cand.is_sub, "").map(lambda d: " (" + d.strip() + ")" if d.strip() else "")
cand["attacker_won_fight"] = cand.FIGHTER == cand.winner
out = pd.DataFrame(
    {
        "fight_id": cand.fight_id,
        "event": cand.EVENT,
        "date": cand.date,
        "attacker": cand.FIGHTER,
        "defender": cand.defender,
        "round": cand["round"],
        "sub_att_count": cand.sub_att,
        "attempt_type": "UNKNOWN_needs_video_review",
        "fight_result_method": cand.fight_result_method,
        "attacker_won_fight": cand.attacker_won_fight,
        "weight_class": cand.WEIGHTCLASS,
        "ufcstats_url": cand.URL,
    }
).sort_values(["date", "fight_id", "round"], ascending=[False, True, True])
out.to_csv(HERE / "failed_attempt_candidates.csv", index=False)

# ---- 3. summary -------------------------------------------------------------
n_sub_fin = int(res.is_sub.sum())
n_rnc = len(succ)
non_finish_att = int(out.sub_att_count.sum())
stats = {
    "n_fights_total": int(len(res)),
    "n_submission_finishes": n_sub_fin,
    "n_rnc_finishes": n_rnc,
    "n_rnc_standard": int((succ.rnc_variant == "standard").sum()),
    "n_rnc_technical_submission": int((succ.rnc_variant != "standard").sum()),
    "rnc_share_of_sub_finishes": round(n_rnc / n_sub_fin, 3),
    "year_min": int(pd.to_datetime(succ.date).dt.year.min()),
    "year_max": int(pd.to_datetime(succ.date).dt.year.max()),
    "median_finish_round": float(succ["round"].median()),
    "round_distribution": {int(k): int(v) for k, v in succ["round"].value_counts().sort_index().items()},
    "median_finish_time_s": float(succ.finish_time_in_round_s.median()),
    "rnc_per_year": {int(k): int(v) for k, v in pd.to_datetime(succ.date).dt.year.value_counts().sort_index().items()},
    "rnc_since_2015": int((pd.to_datetime(succ.date).dt.year >= 2015).sum()),
    "candidate_rows_fighter_rounds": int(len(out)),
    "candidate_fights": int(out.fight_id.nunique()),
    "candidate_total_sub_att": non_finish_att,
    "stats_rows_unmatched_to_results": int(unmatched),
    "est_failed_sub_att_per_sub_finish": round(non_finish_att / n_sub_fin, 2),
    "est_rnc_failed_attempts_if_rnc_share_holds": int(round(non_finish_att * n_rnc / n_sub_fin)),
}
(HERE / "summary_stats.json").write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
