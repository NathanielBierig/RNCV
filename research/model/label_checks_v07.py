"""Raw label cross-checks for MODEL_SPEC v0.7 (owner review of the v0.6 weights): finish rate per level, with Wilson
95% CIs. Two views: the state at the 2-s landmark (one row per attempt), and "ever reached during the attempt"
(descriptive only: longer attempts reach more states, and finishes end the attempt).

    python research/model/label_checks_v07.py
"""
from collections import defaultdict

import state_model as sm

rows = sm.load()


def line(name, ys):
    k, n = sum(ys), len(ys)
    lo, hi = sm.wilson(k, n)
    return f"  {name:34s} {k:2d}/{n:<2d} = {100 * k / n:3.0f}%  [{100 * lo:3.0f}-{100 * hi:3.0f}%]" if n else f"  {name:34s} 0/0"


def table(title, key):
    print(title)
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(r["outcome"] in sm.SUCCESS)
    for k in sorted(g, key=str):
        print(line(str(k), g[k]))
    print()


def ever(r, field, values):
    st = [r.get(field if field != "rnc_style" else "rnc_style_at_L", "")] + [v for _, k, v in sm.changes(r) if k == field]
    return any(v in values for v in st)


print(f"{len(rows)} attempts (bell excluded), {sum(r['outcome'] in sm.SUCCESS for r in rows)} finishes; finish-enriched sample\n")
table("1. Grip style at the 2-s landmark:", lambda r: r["rnc_style_at_L"])
table("1b. Grip style ever reached (descriptive; finishes often switch to figure-four late):",
      lambda r: "figure_four ever" if ever(r, "rnc_style", {"figure_four"}) else
      ("other lock ever (no f4)" if ever(r, "rnc_style", {"palm_to_palm", "gable", "wrist_pull"}) else "never locked / unclear"))
table("1c. Grip at landmark, arm under the chin only:", lambda r: r["rnc_style_at_L"] if r["choke_arm_position"] == "under_chin" else "(not under chin)")
table("2. Choking hand tucked x defender two-on-one (landmark):",
      lambda r: f"hand tucked={r['choking_hand_tucked']}, 2-on-1={r['defender_two_on_one']}")
table("3. Legs at the landmark:", lambda r: r["control"])
table("3b. Legs ever reached:", lambda r: "body triangle ever" if ever(r, "control", {"body_triangle"}) else
      ("two hooks ever (no BT)" if ever(r, "control", {"two_hooks"}) else "one hook / none only"))

print("4. Re-attacks: attempt number within the round (by video time)")
byr = defaultdict(list)
for r in rows:
    byr[(r["fight_id"], r["round"])].append(r)
num = {}
for rs in byr.values():
    for i, r in enumerate(sorted(rs, key=lambda q: float(q["video_time_start"]))):
        num[id(r)] = (i + 1, len(rs))
for via in ("finish_list", "candidate_round"):
    g = defaultdict(list)
    for r in rows:
        if r["found_via"] == via:
            i, n = num[id(r)]
            g["1st attempt" if i == 1 else "2nd+ attempt"].append(r["outcome"] in sm.SUCCESS)
    print(f" found_via = {via}:")
    for k in sorted(g):
        print(line(k, g[k]))
last = [r["outcome"] in sm.SUCCESS for r in rows if num[id(r)][0] == num[id(r)][1] and num[id(r)][1] > 1 and r["found_via"] == "finish_list"]
notlast = [r["outcome"] in sm.SUCCESS for r in rows if num[id(r)][0] < num[id(r)][1] and r["found_via"] == "finish_list"]
print(line("finish-list rounds: LAST attempt", last))
print(line("finish-list rounds: earlier attempts", notlast))
print("  -> by construction: a finish-list round ends with the finish, so its last attempt is always the success and every\n"
      "     earlier one a failure. Re-attack effects can't be tested on these labels (needs random_fight rounds).")
