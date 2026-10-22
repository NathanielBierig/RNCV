"""Findability-ranked list of RNC finishes to label next: title fights, main events and co-mains
first (they're the ones with official video online, and the best quality).

Source: all UFC RNC finishes (rnc_successes.csv), men's divisions only (A1), 2018 or later, not yet
labeled, attackers under the A4 cap (5 attacking rounds, counting labels.csv). Card position comes
from raw_sources/ufc_fight_results.csv, where each event's bouts are listed main event first.
Writes phase3_labels/labeling_queue_findable.csv with the round clock to jump to (60 s before the finish).

Sampling note: picking by findability favors star and title fights. That is allowed for the
hand-picked success list (PREREG §2), and `found_via` stays `finish_list`; report the card-position
mix in the write-up.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python -I phase3_labels/build_findable.py
"""
import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIERS = ["title", "main_event", "co_main", "main_card", "prelim"]

pos, seen = {}, Counter()
for r in csv.DictReader(open(HERE / "raw_sources/ufc_fight_results.csv", encoding="utf-8")):
    fid, ev = r["URL"].rstrip("/").split("/")[-1], r["EVENT"].strip()
    i = seen[ev]; seen[ev] += 1
    pos[fid] = "title" if "title" in r["WEIGHTCLASS"].lower() else \
        ("main_event" if i == 0 else "co_main" if i == 1 else "main_card" if i < 5 else "prelim")

labels = list(csv.DictReader(open(HERE / "labels.csv", encoding="utf-8")))
done = {r["fight_id"] for r in labels}
rounds = Counter(a for a, _, _ in {(r["attacker"], r["fight_id"], r["round"]) for r in labels})

out = []
for r in csv.DictReader(open(HERE / "rnc_successes.csv", encoding="utf-8")):
    if "women" in r["weight_class"].lower() or r["date"] < "2018" or r["fight_id"] in done \
            or rounds[r["winner_attacker"]] >= 5 or r.get("finish_status", "valid") != "valid":
        continue
    fin = int(r["finish_time_in_round_s"] or 0)
    jump = max(0, fin - 60)
    out.append({
        "card_position": pos.get(r["fight_id"], "prelim"),
        "numbered_event": "yes" if r["event"].split(":")[0].strip()[4:].isdigit() else "no",
        "date": r["date"], "event": r["event"], "attacker": r["winner_attacker"], "defender": r["defender"],
        "round": r["round"], "finish": r["finish_time_in_round"], "known_finish_elapsed_s": fin, "found_via": "finish_list",
        "jump_to_clock_remaining": f"{(300 - jump) // 60}:{(300 - jump) % 60:02d}",
        "weight_class": r["weight_class"], "fight_id": r["fight_id"],
        "youtube_search": "https://www.youtube.com/@UFC/search?query=" + "+".join(f"{r['fighter_1']} {r['fighter_2']}".split()),
        "ufcstats_url": r["ufcstats_url"], "status": "todo"})
# Tier first, numbered (PPV) events first, then newest first (better video quality).
out = sorted(out, key=lambda r: (TIERS.index(r["card_position"]), r["numbered_event"] != "yes", -int(r["date"].replace("-", ""))))
for i, r in enumerate(out, 1):
    r["findable_rank"] = i
cols = ["findable_rank"] + [c for c in out[0] if c != "findable_rank"]
with open(HERE / "labeling_queue_findable.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
print(len(out), "rows;", dict(Counter(r["card_position"] for r in out)))
