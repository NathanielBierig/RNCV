"""No-pose RNC attempt detector: CLIP image features + logistic regression, leave-one-fight-out.

For every clip referenced in phase3_labels/labels.csv (plus fully watched no-RNC rounds), frames are
sampled at FPS_S per second. Label = 1 if the frame lies inside a labeled attempt window
[video_time_start, video_time_end], else 0. Each frame -> CLIP ViT-B-32 embedding (laion2b, CPU),
cached in data/attempt_clf/feats.npz. Then: train on all fights but one, test on the held-out fight,
for every fight. Reports frame-level ROC-AUC / PR-AUC per fold and pooled, with and without
temporal smoothing (moving average over ~2 s).

    C:/Users/netan/.venvs/clip/Scripts/python -I research/attempt_clf/attempt_clf.py [--crop] [--refresh]
"""
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FPS_S = 2.0
CROP = "--crop" in sys.argv          # crop each frame to the fighters (pair box) instead of the whole frame
CACHE = ROOT / ("data/attempt_clf/feats_crop.npz" if CROP else "data/attempt_clf/feats.npz")
REPORT = ROOT / ("reports/attempt_clf_crop.md" if CROP else "reports/attempt_clf.md")


def pair_crop(det, frame, pad=0.25):
    """Crop to the fighters: union of the person boxes that overlap the top-scoring box
    (the pile), padded. Person boxes are reliable even when skeletons are mixed. Falls back
    to the full frame when nobody is detected."""
    det(frame, nms_thr=0.65, score_thr=0.25)
    b = det.last_boxes
    if not len(b):
        return frame
    top = b[0]
    keep = [x for x in b if not (x[2] < top[0] or x[0] > top[2] or x[3] < top[1] or x[1] > top[3])]
    x0, y0 = min(x[0] for x in keep), min(x[1] for x in keep)
    x1, y1 = max(x[2] for x in keep), max(x[3] for x in keep)
    w, h = x1 - x0, y1 - y0
    H, W = frame.shape[:2]
    x0, y0 = int(max(0, x0 - pad * w)), int(max(0, y0 - pad * h))
    x1, y1 = int(min(W, x1 + pad * w)), int(min(H, y1 + pad * h))
    return frame[y0:y1, x0:x1] if x1 > x0 + 10 and y1 > y0 + 10 else frame
# Fully watched rounds with no RNC: all frames are negatives (clip name -> fight id).
NEG_CLIPS = {"f22_pimblett_leavitt_r1.mp4": "8e02bdaac8ed50e5"}


def clips_and_windows():
    rows = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
    clips = {}
    for r in rows:
        c = clips.setdefault(r["video_url"], {"fight": r["fight_id"], "win": []})
        c["win"].append((float(r["video_time_start"]), float(r["video_time_end"])))
    for name, fid in NEG_CLIPS.items():
        if (ROOT / "data/clips" / name).exists():
            clips.setdefault(name, {"fight": fid, "win": []})
    return {k: v for k, v in clips.items() if (ROOT / "data/clips" / k).exists()}


def extract(clips):
    import open_clip
    import torch
    from PIL import Image
    model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()
    det = None
    if CROP:
        sys.path.insert(0, str(ROOT / "src"))
        from yolo_pose_onnx import YoloPoseOnnx
        det = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    X, y, fight, clip_id, t_s = [], [], [], [], []
    for ci, (name, info) in enumerate(sorted(clips.items())):
        cap = cv2.VideoCapture(str(ROOT / "data/clips" / name))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(round(fps / FPS_S)))
        i, batch, meta = 0, [], []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            if i % step == 0:
                t = i / fps
                g = pair_crop(det, f) if det is not None else f
                batch.append(prep(Image.fromarray(cv2.cvtColor(g, cv2.COLOR_BGR2RGB))))
                meta.append(t)
            i += 1
            if len(batch) == 32:
                with torch.no_grad():
                    e = model.encode_image(torch.stack(batch)).float()
                X.append((e / e.norm(dim=-1, keepdim=True)).numpy()); t_s += meta; batch, meta = [], []
        if batch:
            with torch.no_grad():
                e = model.encode_image(torch.stack(batch)).float()
            X.append((e / e.norm(dim=-1, keepdim=True)).numpy()); t_s += meta
        n_new = len(t_s) - len(y)
        ts = t_s[-n_new:]
        y += [int(any(a <= t <= b for a, b in info["win"])) for t in ts]
        fight += [info["fight"]] * n_new
        clip_id += [ci] * n_new
        print(f"{name}: {n_new} frames, {sum(y[-n_new:])} inside attempts", flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE, X=np.concatenate(X), y=np.array(y), fight=np.array(fight),
                        clip=np.array(clip_id), t=np.array(t_s))


def smooth(p, clip, k):
    out = p.copy()
    for c in np.unique(clip):
        m = clip == c
        out[m] = np.convolve(p[m], np.ones(k) / k, mode="same")
    return out


def evaluate():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    d = np.load(CACHE)
    X, y, fight, clip = d["X"], d["y"], d["fight"], d["clip"]
    p = np.full(len(y), np.nan)
    lines = ["# No-pose RNC attempt detector (CLIP ViT-B-32 + logistic regression)" + (", fighter crop" if CROP else ""), "",
             f"Frames sampled at {FPS_S}/s from every labeled clip (+ watched no-RNC rounds). Positive = inside a labeled attempt window. "
             "**Leave-one-fight-out:** each fight is scored by a model that never saw it.", "",
             "| Held-out fight | Frames | % inside attempts | ROC-AUC | PR-AUC (base rate) |", "|---|---|---|---|---|"]
    for f in np.unique(fight):
        te = fight == f
        if y[~te].min() == y[~te].max():
            continue
        clf = LogisticRegression(C=0.5, max_iter=2000, class_weight="balanced").fit(X[~te], y[~te])
        p[te] = clf.predict_proba(X[te])[:, 1]
        auc = roc_auc_score(y[te], p[te]) if 0 < y[te].sum() < te.sum() else float("nan")
        ap = average_precision_score(y[te], p[te]) if y[te].sum() else float("nan")
        lines.append(f"| {f[:8]} | {te.sum()} | {100 * y[te].mean():.0f}% | {auc:.2f} | {ap:.2f} ({y[te].mean():.2f}) |")
    ok = ~np.isnan(p)
    ps = smooth(np.nan_to_num(p), clip, 5)
    lines += ["", f"**Pooled (all held-out frames):** ROC-AUC **{roc_auc_score(y[ok], p[ok]):.2f}**, PR-AUC **{average_precision_score(y[ok], p[ok]):.2f}** "
              f"(base rate {y[ok].mean():.2f}). With ~2 s smoothing: ROC-AUC {roc_auc_score(y[ok], ps[ok]):.2f}, PR-AUC {average_precision_score(y[ok], ps[ok]):.2f}.",
              "", "ROC-AUC 0.5 = guessing, 1.0 = perfect. PR-AUC is compared to the base rate (a guesser scores the base rate).",
              "Caveat: few fights, and some clips are almost all attempt (few negatives), so per-fight AUCs are noisy or undefined (nan)."]
    out = REPORT
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-5:]))


if __name__ == "__main__":
    if not CACHE.exists() or "--refresh" in sys.argv:
        extract(clips_and_windows())
    evaluate()
