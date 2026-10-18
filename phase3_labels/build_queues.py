"""PREREG v0.2 section 2: hybrid sampling. Builds labeling_queue_successes.csv,
labeling_queue_failures.csv and random_10.csv.  Run: .venv/Scripts/python -I build_queues.py

Order of operations (so every attempt has exactly one found_via):
 1. random_10: 10 fights drawn uniformly (SEED) from the 2018+ frame = fights in rnc_successes.csv or
    failed_attempt_candidates.csv.  Exempt from caps and never trimmed.
 2. successes queue: valid standard RNC finishes 2018+, not in random_10, recent first.
 3. failures queue: candidate rounds with sub_att >= 2 whose attacker has >= 1 RNC win BEFORE the event
    (fighter_priors.csv, as of event date - 1), not in random_10, ordered by year (recent first) then
    attacker's shrunk RNC-win rate.
 Caps (PREREG): <= 3 attempts per attacker and <= 3 per defender, counted jointly across both queues
 (successes take their slots first).
"""
from pathlib import Path
from urllib.parse import quote_plus

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 20261019
CAP = 3
SESSION1 = {"successes": 8, "failures": 7}

s = pd.read_csv(HERE / "rnc_successes.csv", parse_dates=["date"])
c = pd.read_csv(HERE / "failed_attempt_candidates.csv", parse_dates=["date"])
pri = pd.read_csv(HERE / "fighter_priors.csv")


def search(a, b):
    return "https://www.youtube.com/@UFC/search?query=" + quote_plus(f"{a} {b} full fight")


# ---- 1. random_10 -------------------------------------------------------------
fr = {}
for r in s[s.date.dt.year >= 2018].itertuples():
    fr[r.fight_id] = dict(event=r.event, date=r.date, fighters=f"{r.fighter_1} vs. {r.fighter_2}", weight_class=r.weight_class,
                          url=r.ufcstats_url, rounds={int(r.round)}, finish=f"R{r.round} {r.finish_time_in_round}",
                          in_finish_list=True, a=r.fighter_1, b=r.fighter_2)
for r in c[c.date.dt.year >= 2018].itertuples():
    f = fr.setdefault(r.fight_id, dict(event=r.event, date=r.date, fighters=f"{r.attacker} vs. {r.defender}", weight_class=r.weight_class,
                                       url=r.ufcstats_url, rounds=set(), finish="", in_finish_list=False, a=r.attacker, b=r.defender))
    f["rounds"].add(int(r.round))
frame = pd.DataFrame([dict(fight_id=k, **v) for k, v in fr.items()]).sort_values("fight_id").reset_index(drop=True)
rng = np.random.default_rng(SEED)
pick = frame.iloc[np.sort(rng.choice(len(frame), 10, replace=False))].copy()
rand = pd.DataFrame({
    "fight_id": pick.fight_id, "event": pick.event, "date": pick.date.dt.date, "fighters": pick.fighters,
    "weight_class": pick.weight_class, "found_via": "random_fight",
    "rounds_with_scored_sub_att_or_rnc_finish": pick.rounds.map(lambda r: ";".join(map(str, sorted(r)))),
    "known_rnc_finish": pick.finish, "watch_scope": "FULL FIGHT: label every RNC attempt in every round",
    "ufc_youtube_channel_search": [search(a, b) for a, b in zip(pick.a, pick.b)],
    "ufcstats_url": pick.url, "seed": SEED, "frame_size": len(frame), "status": "todo",
}).sort_values("date", ascending=False)
rand.to_csv(HERE / "random_10.csv", index=False)
exclude = set(pick.fight_id)

# ---- 2. successes queue ---------------------------------------------------------
cnt_att, cnt_def = {}, {}


def take(att, dfn):
    if cnt_att.get(att, 0) >= CAP or cnt_def.get(dfn, 0) >= CAP:
        return False
    cnt_att[att] = cnt_att.get(att, 0) + 1
    cnt_def[dfn] = cnt_def.get(dfn, 0) + 1
    return True


ss = s[(s.date.dt.year >= 2018) & (s.finish_status == "valid") & ~s.fight_id.isin(exclude)].sort_values("date", ascending=False)
rows = []
for r in ss.itertuples():
    if not take(r.winner_attacker, r.defender):
        continue
    t = int(r.finish_time_in_round_s)
    j = max(0, t - 60)
    rows.append(dict(
        queue_rank=len(rows) + 1, session=1 if len(rows) < SESSION1["successes"] else "",
        fight_id=r.fight_id, event=r.event, date=r.date.date(), year=r.date.year,
        attacker=r.winner_attacker, defender=r.defender, round=int(r.round),
        known_finish_elapsed=r.finish_time_in_round, known_finish_elapsed_s=t,
        jump_to_elapsed_s=j, jump_to_clock_remaining=f"{(300 - j) // 60}:{(300 - j) % 60:02d}",
        jump_note="elapsed-in-round seconds = finish - 60; clock_remaining assumes a 5:00 round (broadcast clock counts down)",
        rnc_variant=r.rnc_variant, finisher_sub_att_in_finish_round=r.finisher_sub_att_in_finish_round,
        found_via="finish_list", ufc_youtube_channel_search=search(r.winner_attacker, r.defender),
        fight_pass_lookup=f"UFC Fight Pass: {r.event}", free_full_fight_on_ufc_youtube="unverified",
        ufcstats_url=r.ufcstats_url, status="todo"))
succ_q = pd.DataFrame(rows)
succ_q.to_csv(HERE / "labeling_queue_successes.csv", index=False)

# ---- 3. failures queue ----------------------------------------------------------
cc = c[(c.date.dt.year >= 2018) & (c.sub_att_count >= 2) & ~c.fight_id.isin(exclude)].merge(
    pri[["fight_id", "fighter", "n_prior_rnc_wins", "n_prior_sub_wins", "n_prior_fights", "rnc_win_rate_shrunk"]].rename(columns={"fighter": "attacker"}),
    on=["fight_id", "attacker"], how="left")
n_sub2 = len(cc)
cc = cc[cc.n_prior_rnc_wins >= 1].copy()
cc["year"] = cc.date.dt.year
cc = cc.sort_values(["year", "rnc_win_rate_shrunk", "sub_att_count"], ascending=[False, False, False])
rows = []
for r in cc.itertuples():
    if not take(r.attacker, r.defender):
        continue
    rows.append(dict(
        queue_rank=len(rows) + 1, session=1 if len(rows) < SESSION1["failures"] else "",
        fight_id=r.fight_id, event=r.event, date=r.date.date(), year=r.year,
        attacker=r.attacker, defender=r.defender, round=int(r.round), sub_att_count=int(r.sub_att_count),
        attacker_prior_rnc_wins=int(r.n_prior_rnc_wins), attacker_prior_sub_wins=int(r.n_prior_sub_wins),
        attacker_prior_fights=int(r.n_prior_fights), attacker_rnc_win_rate_shrunk=round(r.rnc_win_rate_shrunk, 4),
        fight_result_method=r.fight_result_method, row_kind=r.row_kind,
        watch_scope=f"round {int(r.round)} only; attempt type unknown, may not contain an RNC (log 0 attempts if none)",
        found_via="candidate_round", ufc_youtube_channel_search=search(r.attacker, r.defender),
        fight_pass_lookup=f"UFC Fight Pass: {r.event}", free_full_fight_on_ufc_youtube="unverified",
        ufcstats_url=r.ufcstats_url, status="todo"))
fail_q = pd.DataFrame(rows)
fail_q.to_csv(HERE / "labeling_queue_failures.csv", index=False)

print("frame fights 2018+:", len(frame), "| random_10 written (seed", SEED, ")")
print("successes queue:", len(succ_q), "| by year:", succ_q.year.value_counts().sort_index().to_dict())
print("failure rounds with sub_att>=2 (2018+, not random):", n_sub2, "| with attacker prior RNC win:", len(cc), "| queue after caps:", len(fail_q))
print("failures by year:", fail_q.year.value_counts().sort_index().to_dict())
print("distinct attackers s/f:", succ_q.attacker.nunique(), fail_q.attacker.nunique())
