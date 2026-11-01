"""Re-download labeled clips whose video was deleted, from the exact link in downloads_log.csv (local only, data/clips/restored/).

    python tools/restore_clips.py

Only exact video ids: another upload of the same fight would shift the labeled timestamps. Skips anything already on disk.
"""
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/clips/restored"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OUT.mkdir(parents=True, exist_ok=True)
    labeled = {r["video_url"] for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))}
    disk = {p.name for p in (ROOT / "data/clips").rglob("*")}
    links = {r["file"]: r["video_id"] for r in csv.DictReader(open(ROOT / "phase3_labels/downloads_log.csv", encoding="utf-8"))
             if r["result"] == "downloaded" and r["file"]}
    got = bad = 0
    for name, vid in sorted(links.items()):
        if name not in labeled or name in disk:
            continue
        stem = name.rsplit(".", 1)[0]
        ok = subprocess.run(["yt-dlp", "-q", "--no-playlist", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                             "-o", str(OUT / f"{stem}.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"]).returncode == 0
        print(name, "OK" if ok else "FAILED", flush=True)
        got += ok
        bad += not ok
    print(f"restored {got}, failed {bad}")


if __name__ == "__main__":
    main()
