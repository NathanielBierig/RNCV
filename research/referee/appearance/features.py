"""Appearance features for every cached RTMO detection (all stride-5 frames of all clips).

    python -I research/referee/appearance/features.py

Reads data/referee/dets/<clip>.npz (made by eval/extract.py) and the clip video, and
writes data/referee/feats/<clip>.npz with, per detection (flattened in frame order):
frame, person_idx, CLIP probabilities per prompt group, CLIP image embedding, and the
clothing (skin-fraction) features from referee.py. CPU only; nothing leaves the laptop.
"""
import glob
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import referee as rf  # noqa: E402

PROMPTS = {
    "referee": ["a photo of a referee wearing a black shirt and black trousers",
                "a person in a black uniform and black gloves",
                "a man wearing a black polo shirt"],
    "fighter": ["a photo of a shirtless MMA fighter wearing shorts",
                "two shirtless men wrestling on the floor",
                "bare skin of a shirtless man's back and arms"],
    "crowd": ["spectators in the crowd behind a fence",
              "a blurry background with no person"],
}
GROUPS = list(PROMPTS)


def square_crop(img, box, pad=0.1):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx, cy, side = (x0 + x1) / 2, (y0 + y1) / 2, max(16.0, max(w, h) * (1 + 2 * pad))
    H, W = img.shape[:2]
    a0, b0 = int(cx - side / 2), int(cy - side / 2)
    a1, b1 = a0 + int(side), b0 + int(side)
    out = np.full((b1 - b0, a1 - a0, 3), 127, np.uint8)
    sx0, sy0, sx1, sy1 = max(0, a0), max(0, b0), min(W, a1), min(H, b1)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - b0:sy1 - b0, sx0 - a0:sx1 - a0] = img[sy0:sy1, sx0:sx1]
    return out


def kpt_box(k, s):
    p = k[s >= rf.THR] if (s >= rf.THR).sum() >= 3 else k
    return np.r_[p.min(0), p.max(0)]


def main():
    import open_clip
    from PIL import Image
    torch.set_num_threads(8)
    model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    tok = open_clip.get_tokenizer("ViT-B-32")
    model.eval()
    with torch.no_grad():
        txt = model.encode_text(tok([p for g in GROUPS for p in PROMPTS[g]]))
        txt = txt / txt.norm(dim=-1, keepdim=True)
    owner = np.array([gi for gi, g in enumerate(GROUPS) for _ in PROMPTS[g]])
    out_dir = ROOT / "data/referee/feats"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(glob.glob(str(ROOT / "data/referee/dets/*.npz"))):
        name = Path(f).stem
        z = np.load(f, allow_pickle=True)
        want = {int(i): (k, s) for i, k, s in zip(z["frame_idx"], z["kpts"], z["scores"])}
        cap = cv2.VideoCapture(str(ROOT / "data/clips" / f"{name}.mp4"))
        rows, crops, i = [], [], 0
        while True:
            ok, img = cap.read()
            if not ok:
                break
            if i in want:
                K, S = want[i]
                for j, (k, s) in enumerate(zip(K, S)):
                    cf = rf.clothing_features(img, k, s)
                    cf["rule"] = rf.referee_score(img, k, s)
                    rows.append({"frame": i, "person_idx": j, **cf})
                    crops.append(prep(Image.fromarray(cv2.cvtColor(square_crop(img, kpt_box(k, s)), cv2.COLOR_BGR2RGB))))
            i += 1
        cap.release()
        embs = []
        with torch.no_grad():
            for b in range(0, len(crops), 64):
                e = model.encode_image(torch.stack(crops[b:b + 64]))
                embs.append((e / e.norm(dim=-1, keepdim=True)).numpy())
        emb = np.concatenate(embs)
        logits = 100.0 * emb @ txt.numpy().T
        p = np.exp(logits - logits.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
        group_p = np.stack([p[:, owner == g].sum(1) for g in range(len(GROUPS))], 1)
        cols = {c: np.array([r[c] for r in rows], float) for c in rows[0]}
        np.savez_compressed(out_dir / f"{name}.npz", emb=emb.astype(np.float16), clip_p=group_p,
                            groups=np.array(GROUPS), **cols)
        print(name, len(rows), "detections", flush=True)


if __name__ == "__main__":
    main()
