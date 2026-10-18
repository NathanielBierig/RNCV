"""Seeded, year-stratified random draw of fights for the 15-attempt pilot (PREREG section 2).
Frame: fights from 2018 on that are in rnc_successes.csv OR failed_attempt_candidates.csv.
Order: shuffle within each year with SEED, then interleave years round-robin -> one fixed global order.
Watch the 'primary' fights in order; stop at >= 15 RNC attempts labeled (never on a success/failure quota).
Run: .venv/Scripts/python -I draw_pilot.py   (writes pilot_15.csv)
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 20261018
N_PRIMARY_PER_YEAR = 4   # 9 years x 4 = 36 primary
N_RESERVE_PER_YEAR = 2

s = pd.read_csv(HERE / "rnc_successes.csv", parse_dates=["date"])
c = pd.read_csv(HERE / "failed_attempt_candidates.csv", parse_dates=["date"])
s = s[s.date.dt.year >= 2018]
c = c[c.date.dt.year >= 2018]

fights = {}
for r in s.itertuples():
    fights[r.fight_id] = dict(event=r.event, date=r.date, fighters=f"{r.fighter_1} vs. {r.fighter_2}",
                              found_via="rnc_success", rounds={int(r.round)}, finish=f"R{r.round} {r.finish_time_in_round}",
                              url=r.ufcstats_url, weight_class=r.weight_class)
for r in c.itertuples():
    f = fights.setdefault(r.fight_id, dict(event=r.event, date=r.date, fighters=None, found_via="sub_att_candidate",
                                           rounds=set(), finish="", url=r.ufcstats_url, weight_class=r.weight_class))
    if f["fighters"] is None:
        f["fighters"] = f"{r.attacker} vs. {r.defender}"
    if f["found_via"] == "rnc_success":
        f["found_via"] = "rnc_success+sub_att_candidate"
    f["rounds"].add(int(r.round))
frame = pd.DataFrame(
    [dict(fight_id=k, **{kk: vv for kk, vv in v.items()}) for k, v in fights.items()]
).sort_values("fight_id").reset_index(drop=True)   # sorted by id so the draw is reproducible
frame["year"] = frame.date.dt.year
rng = np.random.default_rng(SEED)
order = {}
for y, g in frame.groupby("year"):
    ids = g.fight_id.to_numpy().copy()
    rng.shuffle(ids)
    order[y] = list(ids)
need = N_PRIMARY_PER_YEAR + N_RESERVE_PER_YEAR
rows = []
for rank in range(need):
    for y in sorted(order):
        if rank < len(order[y]):
            rows.append((order[y][rank], y, rank))
sel = pd.DataFrame(rows, columns=["fight_id", "year", "rank_in_year"]).merge(frame, on=["fight_id", "year"])
sel["list"] = np.where(sel.rank_in_year < N_PRIMARY_PER_YEAR, "primary", "reserve")
sel["global_order"] = range(1, len(sel) + 1)
sel["rounds_to_watch"] = sel.rounds.map(lambda r: ";".join(str(x) for x in sorted(r)))
sel["date"] = sel.date.dt.date
sel["seed"] = SEED
out = sel[["global_order", "list", "year", "fight_id", "event", "date", "fighters", "weight_class", "found_via",
           "rounds_to_watch", "finish", "url", "seed"]].rename(columns={"finish": "known_finish", "url": "ufcstats_url"})
out["watch_all_rounds_note"] = "label EVERY RNC attempt in the listed rounds (finish round included)"
from urllib.parse import quote_plus

# No direct video links on purpose: search engines return game footage and third-party re-uploads
# (verified on the first result), so only legitimate *search* entry points are given.
out["ufc_youtube_channel_search"] = out.fighters.map(
    lambda f: "https://www.youtube.com/@UFC/search?query=" + quote_plus(f.replace(" vs.", "") + " full fight"))
out["fight_pass_lookup"] = "UFC Fight Pass / event: " + out.event
out["free_full_fight_on_ufc_youtube"] = "unverified"
out["substituted_for"] = ""
out["status"] = "todo"
out.to_csv(HERE / "pilot_15.csv", index=False)
print(len(frame), "fights in frame;", dict(frame.year.value_counts().sort_index()))
print(out.groupby(["list", "found_via"]).size())
