"""Download the next N findable fights for labeling (local only, data/clips/to_label/, git-ignored).

    python tools/fetch_clips.py [N]               # default 15 finish-list fights (files q<rank>_...)
    python tools/fetch_clips.py [N] --failures    # failure rounds: RNC attempts that didn't finish (f<rank>_...)

Walks phase3_labels/labeling_queue_findable.csv in rank order and skips: fights already labeled or already on
disk, women's bouts (PREREG A1), fights before 2018 (PREREG §2), attackers at the round cap (A4: 5 rounds).
For each, searches YouTube and takes the first result that is from an official UFC channel, mentions both
surnames in the title, runs at least 4 minutes and has no video-game / compilation words in the title
(lessons learned: an EA UFC render and an Allen compilation slipped through by hand). Downloads up to 720p.
Every pick (or why there was none) goes to phase3_labels/downloads_log.csv (titles and links only, no video).
"""
import csv
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "data/clips/to_label"          # new downloads wait here; demos/ holds the kept demo clips
LOG = ROOT / "phase3_labels/downloads_log.csv"
OFFICIAL = re.compile(r"^(UFC|UFC Español|ufcespanol|UFC Brasil|UFC Eurasia|UFC Russia|UFC Europe|UFC India|UFC Arabia|UFC on Paramount\+|UFC and UFC on Paramount\+)$")   # exact case: a fan channel "Ufc" got through
BLOCK = {"VwHu1u7Jc6g", "DG3b4zVAE2w"}   # Allen compilation (2026-10-26); unofficial Urbina-Battle upload, bad view (2026-10-27)
BAD = re.compile(r"best of|interview|countdown|press|highli|ufc ?[45]\b|\bea\b|game|simulation|cpu|compilation|every |all .*(finishes|submissions)|top \d|reaction|breakdown|preview|recap|journey|behind the scenes|predict", re.I)
MIN_SECONDS = 240


def surname(name):
    return name.strip().split()[-1].lower()


def search(att, dfn):
    q = f"ytsearch8:{att} vs {dfn} UFC full fight"
    out = subprocess.run(["yt-dlp", "--flat-playlist", "--print", "%(id)s\t%(channel)s\t%(duration)s\t%(title)s", q],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        vid, ch, dur, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
        t = title.lower()
        try:
            dur = float(dur)
        except ValueError:
            continue
        if vid not in BLOCK and OFFICIAL.match(ch.strip()) and surname(att) in t and surname(dfn) in t and dur >= MIN_SECONDS and not BAD.search(title):
            return vid, ch, int(dur), title
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_want = int(args[0]) if args else 15
    fail = "--failures" in sys.argv            # failure rounds (attempts that didn't finish) instead of finishes
    queue = "labeling_queue_failures.csv" if fail else "labeling_queue_findable.csv"
    rank_col, prefix = ("queue_rank", "f") if fail else ("findable_rank", "q")
    labels = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
    done = {r["fight_id"] for r in labels}
    rounds = Counter()
    for (att, fid, rnd) in {(r["attacker"], r["fight_id"], r["round"]) for r in labels}:
        rounds[att] += 1
    on_disk = {p.name.split("_")[0] for p in (ROOT / "data/clips").rglob(f"{prefix}*")}
    log_exists = LOG.exists()
    logf = open(LOG, "a", encoding="utf-8", newline="")
    w = csv.writer(logf)
    if not log_exists:
        w.writerow(["date_run", "findable_rank", "fight_id", "attacker", "defender", "result", "video_id", "channel", "seconds", "title", "file"])
    import datetime
    today = datetime.date.today().isoformat()
    got = 0
    for r in csv.DictReader(open(ROOT / "phase3_labels" / queue, encoding="utf-8")):
        if got >= n_want:
            break
        rank, att, dfn = r[rank_col], r["attacker"], r["defender"]
        why = None
        if r["fight_id"] in done or f"{prefix}{int(rank):02d}" in on_disk:
            continue
        if fail and r.get("status", "todo") != "todo":
            continue
        if "women" in r["weight_class"].lower():
            why = "skip: women's bout (A1)"
        elif r["date"][:4] < "2018":
            why = "skip: before 2018"
        elif rounds[att] >= 5:
            why = "skip: attacker at the 5-round cap (A4)"
        if why:
            w.writerow([today, rank, r["fight_id"], att, dfn, why, "", "", "", "", ""]); continue
        hit = search(att, dfn)
        if not hit:
            w.writerow([today, rank, r["fight_id"], att, dfn, "no official full video found", "", "", "", "", ""]); logf.flush()
            print(f"#{rank} {att} vs {dfn}: no official video", flush=True)
            continue
        vid, ch, dur, title = hit
        name = f"{prefix}{int(rank):02d}_{surname(att)}_{surname(dfn)}"
        ok = subprocess.run(["yt-dlp", "-q", "--no-playlist", "-f", "bv*[height<=720]+ba/b[height<=720]/b",
                             "--merge-output-format", "mp4", "-o", str(CLIPS / f"{name}.%(ext)s"),
                             f"https://www.youtube.com/watch?v={vid}"]).returncode == 0
        w.writerow([today, rank, r["fight_id"], att, dfn, "downloaded" if ok else "download failed", vid, ch, dur, title, f"{name}.mp4" if ok else ""])
        logf.flush()
        print(f"#{rank} {att} vs {dfn}: {'OK' if ok else 'FAIL'} {ch} {dur // 60} min | {title}", flush=True)
        got += ok
    logf.close()
    print(f"downloaded {got}")


if __name__ == "__main__":
    main()
