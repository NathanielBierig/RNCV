"""Build the referee eval set: RTMO-m detections + person crops + contact sheets.

    C:/Users/netan/.venvs/rncv/Scripts/python -I research/referee/eval/extract.py

1. Runs RTMO-m (score 0.3 / nms 0.65, as in src/pose_smoke.py) on every 5th frame of
   each data/clips/*.mp4 and caches all raw detections to data/referee/dets/<clip>.npz
   (the track-level methods need whole clips, not just the eval frames).
2. Picks ~40 eval frames per clip spread over time, plus the frames saved in
   data/pose/select2/ (incl. sterling 195).
3. Saves per eval frame: the full frame (data/referee/frames/), one crop per detected
   person (data/referee/crops/<clip>_<frame>_<idx>.jpg) and contact sheets with
   numbered boxes for labeling by eye (data/referee/sheets/).
Everything under data/ is local only (git-ignored). Never upload it.
"""
import glob
import re
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402

RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
STRIDE, PER_CLIP = 5, 40
OUT = ROOT / "data" / "referee"
COLORS = [(0, 0, 255), (0, 200, 0), (255, 0, 0), (0, 200, 255), (255, 0, 255), (255, 255, 0),
          (0, 128, 255), (128, 0, 255), (255, 128, 0), (128, 255, 128)]


def kpt_box(k, s, pad=0.1):
    """Box around confident joints (all joints if < 3), padded by `pad` of its size."""
    p = k[s >= tf.THR] if (s >= tf.THR).sum() >= 3 else k
    x0, y0 = p.min(0)
    x1, y1 = p.max(0)
    w, h = x1 - x0, y1 - y0
    return np.array([x0 - pad * w, y0 - pad * h, x1 + pad * w, y1 + pad * h])


def detect_clip(model, clip):
    name = Path(clip).stem
    cache = OUT / "dets" / f"{name}.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return name, list(z["frame_idx"]), list(z["kpts"]), list(z["scores"])
    cap = cv2.VideoCapture(clip)
    idx, K, S, i = [], [], [], 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        if i % STRIDE == 0:
            k, s = model(img, nms_thr=0.65, score_thr=0.3)
            idx.append(i)
            K.append(np.asarray(k, dtype=np.float32).reshape(-1, 17, 2))
            S.append(np.asarray(s, dtype=np.float32).reshape(-1, 17))
        i += 1
    cap.release()
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, frame_idx=np.array(idx), kpts=np.array(K, dtype=object),
                        scores=np.array(S, dtype=object), fps=cv2.VideoCapture(clip).get(cv2.CAP_PROP_FPS))
    return name, idx, K, S


def main():
    from rtmlib import RTMO
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    for d in ("frames", "crops", "sheets"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    rows = []
    for clip in sorted(glob.glob(str(ROOT / "data" / "clips" / "*.mp4"))):
        name, idx, K, S = detect_clip(model, clip)
        print(name, len(idx), "frames detected", flush=True)
        extra = [int(re.search(r"_ref_(\d+)", p).group(1))
                 for p in glob.glob(str(ROOT / "data/pose/select2" / f"{name}_ref_*.jpg"))]
        pick = sorted(set(np.linspace(0, len(idx) - 1, PER_CLIP).round().astype(int)) |
                      {idx.index(f) for f in extra if f in idx})
        cap = cv2.VideoCapture(clip)
        for p in pick:
            f = idx[p]
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ok, img = cap.read()
            if not ok:
                continue
            cv2.imwrite(str(OUT / "frames" / f"{name}_{f}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            H, W = img.shape[:2]
            vis = img.copy()
            for j, (k, s) in enumerate(zip(K[p], S[p])):
                b = kpt_box(k, s)
                x0, y0 = int(max(0, b[0])), int(max(0, b[1]))
                x1, y1 = int(min(W, b[2])), int(min(H, b[3]))
                if x1 > x0 + 2 and y1 > y0 + 2:
                    cv2.imwrite(str(OUT / "crops" / f"{name}_{f}_{j}.jpg"), img[y0:y1, x0:x1])
                rows.append((name, f, j, x0, y0, x1, y1, float(s.mean())))
                c = COLORS[j % len(COLORS)]
                cv2.rectangle(vis, (x0, y0), (x1, y1), c, 3)
                cv2.putText(vis, str(j), (x0 + 6, y0 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 8)
                cv2.putText(vis, str(j), (x0 + 6, y0 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, c, 3)
            cv2.putText(vis, f"{name} {f}", (20, H - 25), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
            cv2.imwrite(str(OUT / "sheets" / f"{name}_{f}.jpg"), cv2.resize(vis, (960, 540)))
        cap.release()
    with open(OUT / "candidates.csv", "w") as fh:
        fh.write("clip,frame,person_idx,x0,y0,x1,y1,mean_score\n")
        for r in rows:
            fh.write(",".join(map(str, r[:7])) + f",{r[7]:.3f}\n")
    print(len(rows), "person crops")


if __name__ == "__main__":
    main()
