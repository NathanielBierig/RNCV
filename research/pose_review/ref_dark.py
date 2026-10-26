"""Why the skin referee filter misses referees on real attempt frames: it IGNORES too-dark pixels.

A black shirt is mostly 'too dark' (Y < 30), so referee_score is decided by the few lit pixels
(arm skin, bald head, highlights), which pass the skin-chroma box. Test on the OLD referee eval set
(research/referee/eval/labels.csv, cached features in data/referee/feats/) how dark fractions differ
between fighters and referees, and whether counting dark pixels as 'not skin' helps.

    python -I research/pose_review/ref_dark.py
"""
import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
CLIPS = ["gsp_bisping", "pantoja_asakura_r2", "sterling_sandhagen"]
REG = ["torso", "uarm", "legs"]


def score(f, n, dark_w):
    """dark_w = how much a too-dark pixel counts as 'not skin' (0 = current referee.py, 1 = fully)."""
    num = den = 0.0
    for r in REG:
        sk, dk, nn = f[f"{r}_skin"][n], f[f"{r}_dark"][n], f[f"{r}_n"][n]
        if nn < 30 or np.isnan(dk):
            continue
        sk = 0.0 if np.isnan(sk) else sk
        w_lit, w_dark = nn * (1 - dk), nn * dk * dark_w
        num += w_lit * sk
        den += w_lit + w_dark
    return 0.5 if den == 0 else 1 - num / den


def main():
    lab = {(r["clip"], int(r["frame"]), int(r["person_idx"])): r["label"]
           for r in csv.DictReader(open(ROOT / "research/referee/eval/labels.csv")) if r["small_box"] != "1"}
    rows = []
    for c in CLIPS:
        f = np.load(ROOT / f"data/referee/feats/{c}.npz")
        key = {(int(a), int(b)): n for n, (a, b) in enumerate(zip(f["frame"], f["person_idx"]))}
        for (cc, fr, j), l in lab.items():
            if cc == c and l in ("fighter", "referee") and (fr, j) in key:
                n = key[(fr, j)]
                rows.append((c, l, f["torso_dark"][n], f["rule"][n], *[score(f, n, w) for w in (0, 0.5, 1)]))
    y = np.array([r[1] == "referee" for r in rows])
    td = np.array([r[2] for r in rows], float)
    print(f"n fighters {(~y).sum()}, referees {y.sum()}")
    print(f"torso too-dark share: fighters median {np.nanmedian(td[~y]):.2f} (90th pct {np.nanpercentile(td[~y], 90):.2f}); "
          f"referees median {np.nanmedian(td[y]):.2f} (10th pct {np.nanpercentile(td[y], 10):.2f})")
    for c in CLIPS:
        m = np.array([r[0] == c for r in rows])
        print(f"  {c}: fighters {np.nanmedian(td[m & ~y]):.2f}, referees {np.nanmedian(td[m & y]):.2f}")
    for i, name in enumerate(["referee.py (dark ignored)", "dark counts 0.5", "dark counts 1.0"]):
        s = np.array([r[4 + i] for r in rows])
        for thr in (0.5, 0.6, 0.7):
            p = s > thr
            print(f"{name:26s} thr {thr}: AUC {roc_auc_score(y, s):.3f}  referees caught {p[y].sum()}/{y.sum()}  "
                  f"fighters flagged {p[~y].sum()}/{(~y).sum()}")


if __name__ == "__main__":
    main()
