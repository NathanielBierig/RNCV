"""Camera angles and cuts for the attempt detector (2026-10-29). Uses the cached CLIP features, no new extraction.

    python -I research/attempt_clf/angles.py      -> research/attempt_clf/angles_output.txt (stdout)

1. Cut detection: a camera cut = a big jump between consecutive frame fingerprints (cosine distance above the
   97th percentile within the clip). Detector v2's "past 2-4 s" context is then averaged only within the current
   shot, so a cut doesn't blend two different camera views.
2. Shot-type tags: each frame is compared (zero-shot) with CLIP text descriptions of broadcast shots: wide shot of
   the octagon, close-up of two fighters grappling, overhead view, slow-motion replay, crowd / corner / referee.
   The similarities become extra features, so the detector knows which kind of view it's looking at.
Same leave-one-fight-out test as detector_v2.py; every variant is reported.
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
sys.argv.append("--crop")
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
import attempt_clf as ac  # noqa: E402
import detector_v2 as d2  # noqa: E402

PROMPTS = {
    "wide": "a wide shot of the whole octagon cage from far away",
    "close": "a close-up of two fighters grappling on the ground",
    "back": "a fighter choking another fighter from behind with his arm around the neck",
    "standing": "two fighters standing and striking",
    "overhead": "an overhead view of the cage from above",
    "replay": "a slow motion replay with a graphic overlay",
    "crowd": "the crowd, a corner team or a referee, not the fight",
}


def text_features():
    import open_clip
    import torch
    model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    tok = open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        e = model.encode_text(tok(list(PROMPTS.values()))).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()


def cuts(X, clip, q=97):
    """Shot id per frame: a new shot starts where consecutive fingerprints jump (per clip)."""
    shot = np.zeros(len(X), int)
    sid = 0
    for c in np.unique(clip):
        idx = np.where(clip == c)[0]
        d = 1 - np.sum(X[idx[1:]] * X[idx[:-1]], axis=1)
        th = np.percentile(d, q) if len(d) else 1
        sid += 1
        shot[idx[0]] = sid
        for k in range(1, len(idx)):
            if d[k - 1] > th:
                sid += 1
            shot[idx[k]] = sid
    return shot


def main():
    X, y, fight, clip, t = d2.load("_crop")
    T = text_features()
    sims = X @ T.T                                       # zero-shot similarity to each shot description
    shot = cuts(X, clip)
    n_cuts = len(np.unique(shot)) - len(np.unique(clip))
    print(f"{len(np.unique(fight))} fights, {len(y)} frames, base rate {y.mean():.2f}; detected cuts: {n_cuts} "
          f"(~1 per {len(y) / max(1, n_cuts) / 2:.0f} s)\n")
    kinds = list(PROMPTS)
    top = sims.argmax(1)
    print("shot type (zero-shot, best match): share of frames / share inside attempts")
    for k, name in enumerate(kinds):
        m = top == k
        print(f"  {name:9s} {100 * m.mean():5.1f}%   inside attempts {100 * y[m].mean() if m.any() else 0:5.1f}%")
    print()
    clips = d2.aligned_clips()
    variants = {
        "v2 baseline (context across cuts)": (d2.context(X, clip), {}),
        "v2 + cut-aware context": (d2.context(X, shot), {}),
        "v2 + shot-type features": (np.hstack([d2.context(X, clip), sims * 10]), {}),
        "v2 + cut-aware + shot-type": (np.hstack([d2.context(X, shot), sims * 10]), {}),
        "shot-type features only (7 numbers)": (sims * 10, {}),
    }
    print(f"{'variant':38s} {'ROC':>5s} {'ROC sm':>6s} {'PR':>5s} | {'good win':>8s} {'overlap':>7s} {'FA/min':>6s}")
    for k, (F, kw) in variants.items():
        p = d2.oof(F, y, fight, **kw)
        ok = ~np.isnan(p)
        ps = ac.smooth(np.nan_to_num(p), clip, 5)
        g, h, fa, th = d2.events(p, y, clip, t, clips)
        print(f"{k:38s} {roc_auc_score(y[ok], p[ok]):5.3f} {roc_auc_score(y[ok], ps[ok]):6.3f} "
              f"{average_precision_score(y[ok], p[ok]):5.3f} | {g:8.2f} {h:7.2f} {fa:6.2f}", flush=True)


if __name__ == "__main__":
    main()
