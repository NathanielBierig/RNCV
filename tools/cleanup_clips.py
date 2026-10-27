"""Delete labeled videos in data/clips/to_label/ whose detector features AND neck crops are saved (local cleanup).

    python -I tools/cleanup_clips.py

Never touches data/clips/demos/ or videos without labels (still to be labeled). While labeling is active
(labels.csv saved in the last 30 min) it only lists candidates, so a video you are still labeling is never removed.
"""
import csv
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = time.time() - (ROOT / "phase3_labels/labels.csv").stat().st_mtime < 30 * 60
labeled = {r["video_url"] for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))}
for f in sorted((ROOT / "data/clips/to_label").glob("*")):
    if f.name in labeled and (ROOT / "data/attempt_clf/clips_crop" / f"{f.name}.npz").exists() \
            and (ROOT / "data/crops" / f.name / "index.csv").exists():
        if ACTIVE:
            print("labeling active, would delete later:", f.name)
            continue
        try:
            f.unlink()
            print("deleted", f.name)
        except PermissionError:
            print("in use, kept for now:", f.name)
