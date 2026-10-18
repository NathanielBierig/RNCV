"""Build RNC success list + failed-attempt candidate list from ufcstats-derived CSVs.

Input : raw_sources/*.csv (Greco1899/scrape_ufc_stats snapshot, GPL-3.0, data scraped from ufcstats.com)
Output: rnc_successes.csv, failed_attempt_candidates.csv, summary_stats.json
Run   : .venv/Scripts/python -I build_candidates.py

v2 (critique #22): Overturned/DQ RNCs kept (flagged), duplicated EVENT+BOUT stats not merged,
defender rows in finish rounds kept, event dates resolved for renamed events.
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


def event_key(name):
    """Fallback join key for renamed events ('Noche UFC: A vs. B' vs 'UFC Fight Night: A vs. B')."""
    return name.split(":", 1)[-1].strip().lower()


def load_results():
    events = pd.read_csv(RAW / "ufc_event_details.csv")
    events["EVENT"] = clean(events["EVENT"])
    events["date"] = pd.to_datetime(events["DATE"].str.strip(), format="%B %d, %Y")
    res = pd.read_csv(RAW / "ufc_fight_results.csv")
    for c in ["EVENT", "BOUT", "METHOD", "DETAILS", "WEIGHTCLASS", "TIME", "OUTCOME"]:
        res[c] = clean(res[c])
    res["fight_id"] = res["URL"].map(fight_id)
    # date: exact event-name match, then fallback on the 'A vs. B' part of the name
    res = res.merge(events[["EVENT", "date"]], on="EVENT", how="left")
    ek = events.assign(k=events.EVENT.map(event_key)).drop_duplicates("k").set_index("k")["date"]
    miss = res.date.isna()
    res.loc[miss, "date"] = res.loc[miss, "EVENT"].map(event_key).map(ek)
    parts = res["BOUT"].str.split(" vs\\. ", n=1, regex=True)
    res["fighter_1"] = parts.str[0].str.strip()
    res["fighter_2"] = parts.str[1].str.strip()
    res["round"] = pd.to_numeric(res["ROUND"], errors="coerce")
    res["finish_time_s"] = res["TIME"].map(mmss)
    res["is_sub"] = res.METHOD == "Submission"
    res["is_rnc_text"] = res.DETAILS.str.startswith("Rear Naked Choke")
    # Overturned / DQ rows whose DETAILS still names an RNC are real chokes; keep, flagged
    res["is_rnc"] = res.is_rnc_text & (res.is_sub | res.METHOD.isin(["Overturned", "DQ"]))
    res["finish_status"] = "valid"
    res.loc[res.is_rnc_text & ~res.is_sub, "finish_status"] = "overturned_or_dq"
    res["rnc_variant"] = res.DETAILS.map(lambda d: "technical_submission" if "Technical" in d else "standard")
    # winner / loser; overturned rows have NC outcome, so use "Failed Drug Test by X" (X = the fighter who
    # did the choke and whose win was overturned) for those
    res["winner"] = None
    res["loser"] = None
    for o, w, l in [("W/L", "fighter_1", "fighter_2"), ("L/W", "fighter_2", "fighter_1")]:
        m = res.OUTCOME == o
        res.loc[m, "winner"] = res.loc[m, w]
        res.loc[m, "loser"] = res.loc[m, l]
    for i, r in res[res.finish_status == "overturned_or_dq"].iterrows():
        mm = re.search(r"by (\w+)", r.DETAILS)
        if mm:
            for a, b in [(r.fighter_1, r.fighter_2), (r.fighter_2, r.fighter_1)]:
                if mm.group(1).lower() in a.lower():
                    res.loc[i, ["winner", "loser"]] = [a, b]
    res["bout_ambiguous"] = res.duplicated(["EVENT", "BOUT"], keep=False)
    return res


def main():
    res = load_results()
    ymd = res.date.dt.date

    # ---- 1. RNC successes -------------------------------------------------------
    rnc = res[res.is_rnc].copy()
    succ = pd.DataFrame(
        {
            "fight_id": rnc.fight_id,
            "event": rnc.EVENT,
            "date": rnc.date.dt.date,
            "fighter_1": rnc.fighter_1,
            "fighter_2": rnc.fighter_2,
            "winner_attacker": rnc.winner,
            "defender": rnc.loser,
            "round": rnc["round"].astype("Int64"),
            "finish_time_in_round": rnc.TIME,
            "finish_time_in_round_s": rnc.finish_time_s,
            "weight_class": rnc.WEIGHTCLASS,
            "rnc_variant": rnc.rnc_variant,
            "method_raw": rnc.METHOD,
            "finish_status": rnc.finish_status,
            "ufcstats_url": rnc.URL,
        }
    )

    # ---- 2. failed-attempt candidates (per fighter-round) -----------------------
    st = pd.read_csv(RAW / "ufc_fight_stats.csv")
    st = st.dropna(subset=["ROUND", "FIGHTER"]).copy()
    for c in ["EVENT", "BOUT", "FIGHTER"]:
        st[c] = clean(st[c])
    st["round"] = st["ROUND"].str.extract(r"(\d+)")[0].astype(int)
    st["sub_att"] = pd.to_numeric(st["SUB.ATT"], errors="coerce").fillna(0).astype(int)
    # bouts listed twice in results (same EVENT+BOUT, different fight ids) can't be told apart in the
    # stats table, so they are not merged (avoids doubled rows)
    uniq = res[~res.bout_ambiguous]
    n_ambiguous_stats = int(st.merge(res[res.bout_ambiguous][["EVENT", "BOUT"]].drop_duplicates(), on=["EVENT", "BOUT"]).shape[0])
    st = st.merge(
        uniq[["EVENT", "BOUT", "fight_id", "date", "winner", "is_sub", "round", "METHOD", "DETAILS", "WEIGHTCLASS", "URL"]]
        .rename(columns={"round": "finish_round"}),
        on=["EVENT", "BOUT"],
        how="inner",
    )
    st = st[st.sub_att > 0].copy()
    st["round_ended_in_sub"] = st.is_sub & (st["round"] == st.finish_round)
    # a row in a finish round is dropped only for the fighter who won (the finisher); the other
    # fighter's attempts in that round did not end the round and stay
    st["is_finisher_row"] = st.FIGHTER == st.winner
    cand = st[~(st.round_ended_in_sub & st.is_finisher_row)].copy()

    def other(row):
        f = [x.strip() for x in row.BOUT.split(" vs. ", 1)]
        return f[1] if row.FIGHTER == f[0] else f[0]

    cand["defender"] = cand.apply(other, axis=1)
    cand["fight_result_method"] = cand.METHOD.fillna("") + cand.DETAILS.fillna("").where(cand.is_sub, "").map(
        lambda d: " (" + d.strip() + ")" if d.strip() else ""
    )
    cand["row_kind"] = "standard"
    cand.loc[cand.round_ended_in_sub, "row_kind"] = "defender_in_finish_round"
    out = pd.DataFrame(
        {
            "fight_id": cand.fight_id,
            "event": cand.EVENT,
            "date": cand.date.dt.date,
            "attacker": cand.FIGHTER,
            "defender": cand.defender,
            "round": cand["round"],
            "sub_att_count": cand.sub_att,
            "attempt_type": "UNKNOWN_needs_video_review",
            "row_kind": cand.row_kind,
            "fight_result_method": cand.fight_result_method,
            "attacker_won_fight": cand.FIGHTER == cand.winner,
            "weight_class": cand.WEIGHTCLASS,
            "ufcstats_url": cand.URL,
        }
    ).sort_values(["date", "fight_id", "round"], ascending=[False, True, True])

    # finisher's own sub_att in the finishing round: >=2 means earlier failed attempts in that round
    fin = st[st.round_ended_in_sub & st.is_finisher_row][["fight_id", "sub_att"]].rename(
        columns={"sub_att": "finisher_sub_att_in_finish_round"}
    )
    succ = succ.merge(fin, on="fight_id", how="left")
    succ["finisher_sub_att_in_finish_round"] = succ["finisher_sub_att_in_finish_round"].astype("Int64")
    succ = succ.sort_values("date", ascending=False)
    succ.to_csv(HERE / "rnc_successes.csv", index=False)
    out.to_csv(HERE / "failed_attempt_candidates.csv", index=False)

    # ---- 3. summary -------------------------------------------------------------
    n_sub_fin = int(res.is_sub.sum())
    n_rnc = len(succ)
    sd = pd.to_datetime(succ.date)
    non_finish_att = int(out.sub_att_count.sum())
    stats = {
        "n_fights_total": int(len(res)),
        "n_submission_finishes": n_sub_fin,
        "n_rnc_finishes_incl_overturned_dq": n_rnc,
        "n_rnc_overturned_or_dq": int((succ.finish_status != "valid").sum()),
        "n_rnc_technical_submission": int((succ.rnc_variant != "standard").sum()),
        "rnc_share_of_sub_finishes": round(n_rnc / n_sub_fin, 3),
        "year_min": int(sd.dt.year.min()),
        "year_max": int(sd.dt.year.max()),
        "median_finish_round": float(succ["round"].median()),
        "round_distribution": {int(k): int(v) for k, v in succ["round"].value_counts().sort_index().items()},
        "median_finish_time_s": float(succ.finish_time_in_round_s.median()),
        "rnc_since_2018": int((sd.dt.year >= 2018).sum()),
        "null_dates_in_successes": int(succ.date.isna().sum()),
        "null_dates_in_results": int(res.date.isna().sum()),
        "candidate_rows_fighter_rounds": int(len(out)),
        "candidate_rows_defender_in_finish_round": int((out.row_kind != "standard").sum()),
        "candidate_fights": int(out.fight_id.nunique()),
        "candidate_total_sub_att": non_finish_att,
        "ambiguous_bouts_not_merged": int(res.bout_ambiguous.sum() // 2),
        "est_failed_sub_att_per_sub_finish": round(non_finish_att / n_sub_fin, 2),
    }
    (HERE / "summary_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
