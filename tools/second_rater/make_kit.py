"""Second-rater kit (PREREG §7: a second rater codes at least 30 attempts; Cohen's kappa per factor).

    python tools/second_rater/make_kit.py          -> tools/second_rater/rater.html
    python tools/second_rater/make_kit.py --score answers.csv     -> agreement per factor

Picks 30 attempts at random (fixed seed; half finishes, half failures where possible) that have a public YouTube
video, and writes one self-contained page: for each attempt, a link that jumps to a few seconds before the labeled
start, the second to pause at (start + 2 s, the study's landmark), and the same questions as the labeler. The page
never shows the outcome or the owner's answers (blind), and saves the rater's answers as a CSV to send back.
Only links, times and fighter names are in the page: no footage.
"""
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
L3 = ROOT / "phase3_labels"
HERE = Path(__file__).parent
SUCCESS = {"tap", "ref_stop", "unconscious"}
IDS = {"q01_moreno_figueiredo2.mp4": "mzJBc5wcxtc", "q02_khabib_mcgregor.mp4": "JuBBIJ7adjM", "q05_silva_delgado.mp4": "5L184TA9VDQ",
       "q07_moicano_duncan.mp4": "-BmqMDT3ERE", "q09_hernandez_dolidze.mp4": "aOnpsiZ5BOA", "q10_tybura_tuivasa.mp4": "AzSY34tjmaM",
       "q12_allen_muniz.mp4": "KLXUfitsCLo", "q13_smith_spann.mp4": "CmAwV68gBHY", "q16_maia_askren.mp4": "ESNeuaZ-K0Q",
       "q70_allen_silva.mp4": "VwHu1u7Jc6g"}                       # first downloads, from FINDABLE_TOP18.md
FIELDS = {
    "choke_arm_position": ("Choking arm", {"under_chin": "under the chin", "over_jaw": "over the jaw", "unclear": "can't tell"}),
    "rnc_style_at_L": ("Grip", {"figure_four": "figure-four", "palm_to_palm": "palm to palm", "gable": "gable", "wrist_pull": "wrist pull",
                                "short_choke": "short choke", "one_arm": "one arm", "unclear": "can't tell"}),
    "control": ("Legs", {"body_triangle": "body triangle", "two_hooks": "both hooks", "one_hook": "one hook", "none": "none", "unclear": "can't tell"}),
    "defender_two_on_one": ("Defender two-on-one", {"True": "yes", "False": "no", "unclear": "can't tell"}),
    "choking_hand_tucked": ("Choking hand hidden", {"True": "yes", "False": "no", "unclear": "can't tell"}),
    "chin_tucked": ("Chin tucked", {"True": "yes", "False": "no", "unclear": "can't tell"}),
    "opponent_flattened": ("Defender flattened", {"True": "yes", "False": "no", "unclear": "can't tell"}),
}
GROUP = {"rnc_style_at_L": {"palm_to_palm": "other_lock", "gable": "other_lock", "wrist_pull": "other_lock",
                            "short_choke": "open", "one_arm": "open"}}   # grips are scored in the model's 3 groups too


def key(r):
    return "|".join([r["fight_id"], r["round"], r["video_url"], r["video_time_start"]])


def load():
    ids = dict(IDS)
    for r in csv.DictReader(open(L3 / "downloads_log.csv", encoding="utf-8")):
        if r.get("file") and r.get("video_id"):
            ids[r["file"]] = r["video_id"]
    rows = [r for r in csv.DictReader(open(L3 / "labels.csv", encoding="utf-8")) if "excluded_" not in r["notes"]]
    return rows, ids


def build():
    rows, ids = load()
    ok = [r for r in rows if r["video_url"] in ids and r["outcome"] != "bell"]
    fin = [r for r in ok if r["outcome"] in SUCCESS]
    fail = [r for r in ok if r["outcome"] not in SUCCESS]
    rng = random.Random(20261101)
    rng.shuffle(fin); rng.shuffle(fail)
    pick = fail[:15]
    pick += fin[:30 - len(pick)]
    rng.shuffle(pick)
    items = []
    for r in pick:
        s = float(r["video_time_start"])
        items.append({"key": key(r), "fight": f"{r['attacker']} vs {r['defender']}", "attacker": r["attacker"],
                      "url": f"https://www.youtube.com/watch?v={ids[r['video_url']]}&t={max(0, int(s) - 4)}s",
                      "start": round(s, 1), "pause": round(s + 2, 1)})
    page = (HERE / "template.html").read_text(encoding="utf-8")
    page = page.replace("/*ITEMS*/[]", json.dumps(items)).replace("/*FIELDS*/{}", json.dumps({k: {"label": v[0], "opts": v[1]} for k, v in FIELDS.items()}))
    (HERE / "rater.html").write_text(page, encoding="utf-8")
    print(f"{len(items)} attempts ({sum(r['outcome'] in SUCCESS for r in pick)} finishes, {len(pick) - sum(r['outcome'] in SUCCESS for r in pick)} failures) from "
          f"{len({r['fight_id'] for r in pick})} fights -> {HERE / 'rater.html'}")


def kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan"), 0.0
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def score(path):
    rows, _ = load()
    mine = {key(r): r for r in rows}
    ans = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    print(f"{len(ans)} rated attempts\n\n{'factor':24s} {'n':>3s} {'agree':>6s} {'kappa':>6s}  verdict (PREREG: kappa < 0.4 = not reliably codable)")
    for f, (label, _) in FIELDS.items():
        a, b = [], []
        for r in ans:
            m = mine.get(r["key"])
            if not m or not r.get(f) or r[f] == "unclear" or m[f] in ("", "unclear"):
                continue
            g = GROUP.get(f, {})
            a.append(g.get(m[f], m[f])); b.append(g.get(r[f], r[f]))
        k, po = kappa(a, b)
        print(f"{label:24s} {len(a):3d} {100 * po:5.0f}% {k:6.2f}  {'ok' if k >= 0.4 else 'NOT reliably codable'}")


if __name__ == "__main__":
    if "--score" in sys.argv:
        score(sys.argv[sys.argv.index("--score") + 1])
    else:
        build()
