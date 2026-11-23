"""Append rounds of known back-riders to labeling_queue_long.csv (existing rows, ranks and statuses are kept).

    python -I phase3_labels/add_backrider_rounds.py

Owner (2026-11-23): Oliveira, Sterling and others stay on the back for a long time, so long clips mean fewer clips to label.
build_long_queue.py keeps one round per attacker; for these fighters every round with 2:00+ of control and a submission
attempt is added (control isn't always back control: a round can still hold no choke). Fighters other than the owner's
picks are the attackers with the most labeled attempts so far. New rows get ranks above the current maximum, so
`tools/fetch_clips.py N --long --min-rank <first new rank>` fetches them first.
"""
import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_long_queue as blq  # noqa: E402

L3 = Path(__file__).resolve().parent
BACKRIDERS = ["Charles Oliveira", "Aljamain Sterling", "Renato Moicano",                      # owner's picks
              "Khamzat Chimaev", "Raoni Barcelos", "Colby Covington", "Deiveson Figueiredo",   # most labeled attempts
              "Brendan Allen", "Jailton Almeida"]
MIN_CONTROL = 120


def main():
    path = L3 / "labeling_queue_long.csv"
    q = list(csv.DictReader(open(path, encoding="utf-8")))
    cols = list(q[0].keys())
    have = {(r["fight_id"], r["round"], r["attacker"]) for r in q}
    s = blq.prep(MIN_CONTROL)
    s = s[s.FIGHTER.isin(BACKRIDERS)].sort_values(["control_s", "sub_att_count"], ascending=False)
    nxt = max(int(r["queue_rank"]) for r in q) + 1
    added = []
    for r in s.itertuples():
        if (r.fight_id, str(r.round), r.FIGHTER) in have:
            continue
        a, b = [x.strip() for x in r.BOUT.split(" vs. ")]
        q.append({"queue_rank": nxt, "fight_id": r.fight_id, "event": r.EVENT, "date": r.date.date().isoformat(), "attacker": r.FIGHTER,
                  "defender": b if r.FIGHTER == a else a, "round": r.round, "sub_att_count": r.sub_att_count, "control_s": r.control_s,
                  "fight_result_method": r.METHOD, "watch_scope": f"round {r.round} only; {r.CTRL} of control; press G on every change; may hold no choke (log 0 attempts if none)",
                  "found_via": "candidate_round", "ufcstats_url": r.URL.strip(), "status": "todo", "weight_class": r.WEIGHTCLASS})
        added.append((nxt, r.FIGHTER, b if r.FIGHTER == a else a, r.date.date().isoformat(), r.round, r.control_s))
        nxt += 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(q)
    for x in added:
        print(*x)
    print(len(added), "rounds added")


if __name__ == "__main__":
    main()
