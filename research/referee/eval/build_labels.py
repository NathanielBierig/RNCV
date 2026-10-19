"""Turn the hand labels (data/referee/raw_labels.txt) into research/referee/eval/labels.csv.

raw_labels.txt line: "<clip> <frame>: <idx>=F|R|J|D<k> ... | free-text note".
People not listed were judged crowd/background (they are also the small boxes that
select()'s crowd rule drops); unlisted non-small people are reported for a re-check.
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402

OUT = ROOT / "data" / "referee"
NAMES = {"F": "fighter", "R": "referee", "J": "crowd_or_junk", "D": "duplicate"}


def main():
    raw = {}
    for line in (OUT / "raw_labels.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        head, _, note = line.partition("|")
        key, _, body = head.partition(":")
        clip, frame = key.split()
        raw[(clip, int(frame))] = (dict(re.findall(r"(\d+)=([FRJ]|D\d+)", body)), note.strip())
    dets = {}
    for f in (OUT / "dets").glob("*.npz"):
        z = np.load(f, allow_pickle=True)
        dets[f.stem] = {int(i): (k, s) for i, k, s in zip(z["frame_idx"], z["kpts"], z["scores"])}
    rows, missing = [], []
    for r in csv.DictReader(open(OUT / "candidates.csv")):
        clip, frame, j = r["clip"], int(r["frame"]), int(r["person_idx"])
        if (clip, frame) not in raw:
            missing.append((clip, frame)); continue
        lab, note = raw[(clip, frame)]
        K, S = dets[clip][frame]
        areas = np.array([tf.box_area(k, s) for k, s in zip(K, S)])
        small = bool(areas[j] < 0.15 * max(areas.max(), 1))
        code = lab.get(str(j))
        if code is None:
            if not small:
                print("unlabeled non-small person:", clip, frame, j)
            label, pnote = "crowd_or_junk", ""
        else:
            label = NAMES[code[0]]
            pnote = f"duplicate of {code[1:]}" if code[0] == "D" else ""
        rows.append({"clip": clip, "frame": frame, "person_idx": j,
                     "x0": r["x0"], "y0": r["y0"], "x1": r["x1"], "y1": r["y1"],
                     "label": label, "small_box": int(small), "mean_kpt_score": r["mean_score"],
                     "notes": "; ".join(x for x in (pnote, note) if x)})
    out = ROOT / "research/referee/eval/labels.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(Counter(r["label"] for r in rows), "frames missing labels:", sorted(set(missing)))


if __name__ == "__main__":
    main()
