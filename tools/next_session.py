"""Rebuild phase3_labels/NEXT_SESSION.md from the videos waiting in data/clips/to_label/.

    python tools/next_session.py

Failure rounds (f<rank>_...) come first, with the round to watch; then finish-list fights (q<rank>_...) with the
finish time. Fan uploads (from downloads_log.csv) are marked so the owner checks them before labeling.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L3 = ROOT / "phase3_labels"


def main():
    F = {r["findable_rank"]: r for r in csv.DictReader(open(L3 / "labeling_queue_findable.csv", encoding="utf-8"))}
    Q = {r["queue_rank"]: r for r in csv.DictReader(open(L3 / "labeling_queue_failures.csv", encoding="utf-8"))}
    chan = {}
    if (L3 / "downloads_log.csv").exists():
        for r in csv.DictReader(open(L3 / "downloads_log.csv", encoding="utf-8")):
            if r.get("file"):
                chan[r["file"]] = r["channel"]
    official = lambda c: c.startswith("UFC") or c.lower().startswith("ufc") or c.startswith("Eurosport")
    src = lambda f: "" if official(chan.get(f, "UFC")) else " ⚠️ fan upload, check it"
    fail, fin = [], []
    for f in sorted(p.name for p in (ROOT / "data/clips/to_label").glob("*.mp4")):
        pre, rk = f[0], f.split("_")[0][1:].lstrip("0")
        if pre == "f" and rk in Q:
            r = Q[rk]
            fail.append(f"| `{r['attacker']}` | {r['attacker']} vs {r['defender']} | {r['event']} ({r['date'][:4]}) | "
                        f"{r['watch_scope'] or 'R' + r['round']} | `{f}`{src(f)} |")
        elif pre == "q" and rk in F:
            r = F[rk]
            fin.append(f"| `#{rk}` | {r['attacker']} vs {r['defender']} | {r['event']} ({r['date'][:4]}) | "
                       f"R{r['round']} {r['finish']} | `{f}`{src(f)} |")
    out = ["# Next session: fights on disk, ready to label", "",
           f"{len(fail) + len(fin)} fights in `data/clips/to_label/`. In the labeler, load **both** fight lists "
           "(`labeling_queue_findable.csv` and `labeling_queue_failures.csv`), then search the name or `#rank`. Label "
           "**every** RNC attempt in the round to watch. Skip any video that isn't the real fight (fan uploads can be "
           "game renders or filmed off a screen) and tell Main.", "",
           "## Failure rounds (top priority: attempts that did NOT finish)", "",
           "| Search | Fight | Event | Round to watch | File |", "|---|---|---|---|---|", *fail, "",
           "## Finish-list fights", "", "| Search | Fight | Event | Finish (elapsed) | File |", "|---|---|---|---|---|", *fin]
    (L3 / "NEXT_SESSION.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(fail)} failure rounds, {len(fin)} finish fights")


if __name__ == "__main__":
    main()
