"""Factor model on tight head/neck crops (the next try after reports/factor_pilot.md).

    python -I research/attempt_clf/factor_neck.py

Input: data/crops/<clip>/ (tools/save_neck_crops.py: 224x224 crops around the fighters' heads, 4 per second,
inside each labeled attempt; local only). Each crop -> CLIP ViT-B-32 image features (cached per clip, plus the
mirrored crop as free extra training data). Target per crop = the factor's labeled value at that moment (2-s panel
plus G-panel changes). Leave-one-fight-out logistic regression, same metrics as the pilot: frame ROC-AUC, and
attempt-level agreement (kappa) with the label at the 2-s landmark. Meaningful from ~30 fights; the M2 bar is
kappa >= 0.4.
"""
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/model"))
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
import state_model as sm  # noqa: E402
from factor_pilot import FACTORS  # noqa: E402

CROPS = ROOT / "data/crops"


def features(clip_dir):
    cache = clip_dir / "feats.npz"
    if cache.exists():
        d = np.load(cache)
        return d["X"], d["Xm"]
    import open_clip
    import torch
    from PIL import Image, ImageOps
    model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()
    files = [r["file"] for r in csv.DictReader(open(clip_dir / "index.csv", encoding="utf-8"))]
    out = []
    for flip in (False, True):
        embs = []
        for k in range(0, len(files), 32):
            ims = [Image.open(clip_dir / f).convert("RGB") for f in files[k:k + 32]]
            ims = [ImageOps.mirror(i) for i in ims] if flip else ims
            with torch.no_grad():
                e = model.encode_image(torch.stack([prep(i) for i in ims])).float()
            embs.append((e / e.norm(dim=-1, keepdim=True)).numpy())
        out.append(np.concatenate(embs) if embs else np.zeros((0, 512), np.float32))
    np.savez_compressed(cache, X=out[0], Xm=out[1])
    return out[0], out[1]


def main():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import cohen_kappa_score, roc_auc_score
    rows = {"|".join([r["fight_id"], r["round"], r["video_url"], r["video_time_start"]]): r
            for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"]}
    X, Xm, fight, key, el = [], [], [], [], []
    for d in sorted(p for p in CROPS.iterdir() if (p / "index.csv").exists()) if CROPS.exists() else []:
        idx = list(csv.DictReader(open(d / "index.csv", encoding="utf-8")))
        if not idx:
            continue
        a, b = features(d)
        for n, r in enumerate(idx):
            row = rows.get(r["row_key"])
            if row is None:
                continue
            X.append(a[n]); Xm.append(b[n]); fight.append(row["fight_id"]); key.append(r["row_key"])
            el.append(float(r["t"]) - float(row["video_time_start"]))
    if not X:
        print("no crops yet: run tools/save_neck_crops.py on labeled clips first"); return
    X, Xm, fight, el = np.array(X), np.array(Xm), np.array(fight), np.array(el)
    print(f"{len(X)} crops, {len(set(key))} attempts, {len(set(fight))} fights"
          + ("  (too few fights for a real result: pipeline check only)" if len(set(fight)) < 15 else "") + "\n")
    print(f"{'factor':40s} {'crops':>6s} {'% pos':>6s} {'ROC':>5s} | {'attempts':>8s} {'kappa':>6s}")
    for fname, (k_, pos, neg) in FACTORS.items():
        y = np.array([1 if (v := sm.state_at(rows[k], max(0.0, e)).get(k_, "")) in pos else 0 if v in neg else -1
                      for k, e in zip(key, el)])
        use = y >= 0
        p = np.full(len(y), np.nan)
        for f in np.unique(fight[use]):
            te, tr = use & (fight == f), use & (fight != f)
            if len(np.unique(y[tr])) < 2:
                continue
            clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced")
            clf.fit(np.vstack([X[tr], Xm[tr]]), np.r_[y[tr], y[tr]])            # mirrored crops = extra data
            p[te] = clf.predict_proba(X[te])[:, 1]
        ok = use & ~np.isnan(p)
        auc = roc_auc_score(y[ok], p[ok]) if len(np.unique(y[ok])) == 2 else float("nan")
        lab, pred = [], []
        for k in sorted(set(np.array(key)[ok])):
            m = ok & (np.array(key) == k) & (el <= 4.0)
            v = sm.state_at(rows[k], sm.LANDMARK).get(k_, "")
            if m.any() and v in pos | neg:
                lab.append(int(v in pos)); pred.append(int(p[m].mean() >= 0.5))
        kap = cohen_kappa_score(lab, pred) if len(set(lab)) > 1 else float("nan")
        print(f"{fname:40s} {ok.sum():6d} {100 * y[ok].mean() if ok.any() else 0:5.0f}% {auc:5.2f} | {len(lab):8d} {kap:6.2f}")


if __name__ == "__main__":
    main()
