"""Can the computer give the odds on its own? (EXPLORATORY)    python research/attempt_clf/auto_odds.py  -> reports/auto_odds.md

No hand-labeled factors: the only input is the image fingerprints (CLIP features of the fighter crop) from the first
seconds of each attempt. Leave-one-fight-out: predict finish or not, and seconds until the choke ends. Compared with
always guessing the training-fights' average and median. Start times still come from labels here, because the detector
can't place the start yet, so this is the best case for the automatic pipeline.
AUC uses p minus the training average: leaving a fight out shifts that average against the held-out outcomes, which
pushes a plain AUC far below 0.5 when predictions barely move.
"""
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
PER = ROOT / "data/attempt_clf/clips_crop"
SUCCESS = {"tap", "ref_stop", "unconscious"}
WINDOWS = (2.0, 4.0, 6.0)
N_PCA = (8, 16)
C = 0.05


def load(win):
    X, y, secs, fight = [], [], [], []
    rows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"] and r["outcome"] != "bell" and r["video_url"]]
    for r in rows:
        p = PER / f"{r['video_url']}.npz"
        if not p.exists():
            continue
        d = np.load(p)
        a, b = float(r["video_time_start"]), float(r["video_time_end"])
        hit = (d["t"] >= a) & (d["t"] <= min(a + win, b))
        if hit.sum() < 2:
            continue
        X.append(d["X"][hit].mean(0))
        y.append(r["outcome"] in SUCCESS)
        secs.append(b - a)
        fight.append(r["fight_id"])
    return np.array(X), np.array(y, float), np.array(secs), np.array(fight)


def lofo(X, y, secs, fight, k):
    p, base, t, tbase = np.zeros(len(y)), np.zeros(len(y)), np.zeros(len(y)), np.zeros(len(y))
    for fid in np.unique(fight):
        te = fight == fid
        pca = PCA(k, random_state=0).fit(X[~te])
        ztr, zte = pca.transform(X[~te]), pca.transform(X[te])
        p[te] = LogisticRegression(C=C, max_iter=3000).fit(ztr, y[~te]).predict_proba(zte)[:, 1]
        base[te] = y[~te].mean()
        t[te] = np.expm1(Ridge(alpha=10.0).fit(ztr, np.log1p(secs[~te])).predict(zte))
        tbase[te] = np.median(secs[~te])
    return p, base, t, tbase


def main():
    out = ["# Automatic odds and timing, no hand labels (exploratory)", "",
           "Input: image fingerprints from the first seconds of each attempt, tested on fights left out of training. "
           "Start times come from labels (best case). Hand-labeled model v0.8 for comparison: Brier 0.244 vs 0.256 at 2 s.", "",
           "| Seconds seen | Fingerprint size | Attempts | Finish AUC | Brier vs guessing the average | Time error (median, s) vs guessing the median |",
           "|---|---|---|---|---|---|"]
    for win in WINDOWS:
        X, y, secs, fight = load(win)
        for k in N_PCA:
            p, base, t, tbase = lofo(X, y, secs, fight, k)
            out.append(f"| {win:g} | {k} | {len(y)} | {roc_auc_score(y, p - base):.2f} | {np.mean((p - y) ** 2):.3f} vs {np.mean((base - y) ** 2):.3f} | "
                       f"{np.median(np.abs(t - secs)):.1f} vs {np.median(np.abs(tbase - secs)):.1f} |")
    sys.path.insert(0, str(ROOT / "research/model"))
    import damage as dm
    stats, rows = dm.stats_by_fight(), [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
                                        if "excluded_" not in r["notes"] and r["outcome"] != "bell"]
    Z, y, fight = [], [], []
    for r in rows:
        d = dm.damage(r, stats)
        Z.append([np.log1p(d[1]), d[0], int(r["round"])])
        y.append(r["outcome"] in SUCCESS)
        fight.append(r["fight_id"])
    Z, y, fight = np.array(Z, float), np.array(y, float), np.array(fight)
    p, base = np.zeros(len(y)), np.zeros(len(y))
    for fid in np.unique(fight):
        te = fight == fid
        p[te] = LogisticRegression(C=1.0, max_iter=3000).fit(Z[~te], y[~te]).predict_proba(Z[te])[:, 1]
        base[te] = y[~te].mean()
    out += ["", "## Public stats only, no vision at all", "", f"Strikes and knockdowns in earlier rounds, plus the round number ({len(y)} attempts, "
            f"fights left out of training): AUC {roc_auc_score(y, p - base):.2f}, Brier {np.mean((p - y) ** 2):.3f} vs {np.mean((base - y) ** 2):.3f}. "
            "Finish-enriched sample, so part of this may come from how fights were picked (`reports/damage.md`)."]
    out += ["", "**How to read it:** image fingerprints don't beat guessing the average on Brier or on time, so the computer can't "
            "give useful odds or timing from pixels yet. An AUC around 0.6 with no Brier gain is not a usable signal."]
    (ROOT / "reports/auto_odds.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
