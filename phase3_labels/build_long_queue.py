"""Long-control rounds for training the automatic readers: labeling_queue_long.csv.    python -I phase3_labels/build_long_queue.py

Public round stats (raw_sources): men's fights from 2018, rounds where one fighter had 3:00+ of control and at least one
submission attempt, longest first, one round per attacker. Control isn't always back control and the attempt isn't always
an RNC, so a round can hold no choke. Picked for computer-vision training, not at random: the science excludes them in a
sensitivity check (PREREG A6).
"""
import csv
from pathlib import Path

import pandas as pd

L3 = Path(__file__).resolve().parent
RAW = L3 / "raw_sources"
MIN_CONTROL = 180
FIRST = ["Renato Moicano"]        # owner's pick: he strings long sequences together (2026-11-01)


def main():
    s = pd.read_csv(RAW / "ufc_fight_stats.csv").dropna(subset=["ROUND", "CTRL"])
    s = s[s.ROUND.astype(str).str.startswith("Round") & s.CTRL.astype(str).str.contains(":")].copy()
    s["control_s"] = s.CTRL.str.split(":").apply(lambda x: int(x[0]) * 60 + int(x[1]))
    s["sub_att_count"] = pd.to_numeric(s["SUB.ATT"], errors="coerce").fillna(0).astype(int)
    s["round"] = s.ROUND.str.split().str[1].astype(int)
    s = s[(s.control_s >= MIN_CONTROL) & (s.sub_att_count >= 1)]
    for c in ("EVENT", "BOUT"):
        s[c] = s[c].str.strip().str.split().str.join(" ")
    ev = pd.read_csv(RAW / "ufc_event_details.csv")
    ev["EVENT"] = ev.EVENT.str.strip().str.split().str.join(" ")
    ev["date"] = pd.to_datetime(ev.DATE, errors="coerce")
    res = pd.read_csv(RAW / "ufc_fight_results.csv")
    det = pd.read_csv(RAW / "ufc_fight_details.csv")
    for d in (res, det):
        for c in ("EVENT", "BOUT"):
            d[c] = d[c].str.strip().str.split().str.join(" ")
    s = s.merge(ev[["EVENT", "date"]], on="EVENT").merge(res[["EVENT", "BOUT", "WEIGHTCLASS", "METHOD"]], on=["EVENT", "BOUT"]) \
         .merge(det[["EVENT", "BOUT", "URL"]], on=["EVENT", "BOUT"])
    s = s[(s.date >= "2018-01-01") & ~s.WEIGHTCLASS.str.contains("Women", case=False, na=False)]
    s["fight_id"] = s.URL.str.strip().str.rsplit("/", n=1).str[-1]
    skip = {r["fight_id"] for r in csv.DictReader(open(L3 / "labels.csv", encoding="utf-8"))}
    s = s[~s.fight_id.isin(skip)]
    s["first"] = s.FIGHTER.isin(FIRST)
    s = s.sort_values(["first", "control_s", "sub_att_count"], ascending=False).drop_duplicates("FIGHTER")
    rows = []
    for i, r in enumerate(s.itertuples(), 1):
        a, b = [x.strip() for x in r.BOUT.split(" vs. ")]
        rows.append({"queue_rank": i, "fight_id": r.fight_id, "event": r.EVENT, "date": r.date.date().isoformat(), "attacker": r.FIGHTER,
                     "defender": b if r.FIGHTER == a else a, "round": r.round, "sub_att_count": r.sub_att_count, "control_s": r.control_s,
                     "fight_result_method": r.METHOD, "watch_scope": f"round {r.round} only; {r.CTRL} of control; press G on every change; may hold no choke (log 0 attempts if none)",
                     "found_via": "candidate_round", "ufcstats_url": r.URL.strip(), "status": "todo", "weight_class": r.WEIGHTCLASS})
    pd.DataFrame(rows).to_csv(L3 / "labeling_queue_long.csv", index=False)
    print(len(rows), "rounds")


if __name__ == "__main__":
    main()
