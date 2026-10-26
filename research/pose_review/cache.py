"""Cache raw pose outputs for the correctness eval (run once; ~10-15 min on CPU).

48 eval frames = 3 per labeled attempt in phase3_labels/labels.csv (start + 2 s, middle, end - 1 s).
For each eval frame we also run the 1 s before it (stride 2) so the 2-slot tracker has history.
Every processed frame gets the raw output of
  RTMO-m  (score 0.3,  nms 0.65)   -> pipeline A, and the fallback of C
  rncv_pose_v1.onnx (score 0.25, nms 0.65) -> pipeline B, C
Saved to data/pose_review/cache.pkl (local, git-ignored); eval frames as JPGs in data/pose_review/frames/.

    python -I research/pose_review/cache.py [--negatives]
"""
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from pose_attempts import RTMO_M  # noqa: E402
from yolo_pose_onnx import YoloPoseOnnx  # noqa: E402
from rtmlib import RTMO  # noqa: E402

OUT = ROOT / "data/pose_review"
WARM_S, STRIDE = 1.0, 2


def eval_times(t0, t1):
    if t1 - t0 >= 3.5:
        return [("start", t0 + 2), ("mid", (t0 + t1) / 2), ("end", t1 - 1)]
    return [("start", t0 + 0.25 * (t1 - t0)), ("mid", (t0 + t1) / 2), ("end", t0 + 0.9 * (t1 - t0))]


def eval_frames():
    lab = pd.read_csv(ROOT / "phase3_labels/labels.csv", dtype=str, keep_default_na=False)
    out = []
    for k, r in lab.iterrows():
        if not (ROOT / "data/clips" / r.video_url).exists():
            continue
        t0, t1 = float(r.video_time_start), float(r.video_time_end)
        for pos, t in eval_times(t0, t1):
            out.append(dict(row=k + 1, clip=r.video_url, pos=pos, t=t, t_attempt0=t0,
                            context=r.back_context, attacker_side=r.attacker_side))
    return out


# Negative frames (outside every labeled attempt window, >= 3 s away) for precision of the role signals.
NEG = {"f21_blachowicz_pereira_r1.mp4": [20, 60, 100, 170, 195, 290], "olivera_hoolowar_r1.mp4": [120, 135, 170, 185],
       "elkins_johnson_r2.mp4": [14, 17], "sterling_sandhagen.mp4": [25, 32], "pantoja_asakura_r2_b.mp4": [5, 12],
       "formiga_nguyen_r3_b.mp4": [5, 10]}


def neg_frames():
    return [dict(row=100 + i, clip=c, pos="neg", t=float(t), t_attempt0=float(t) - 1.0, context="none", attacker_side="")
            for i, (c, t) in enumerate((c, t) for c, ts in NEG.items() for t in ts)]


def main():
    neg = "--negatives" in sys.argv
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    rtmo = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    v1 = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    cache = []
    for e in (neg_frames() if neg else eval_frames()):
        cap = cv2.VideoCapture(str(ROOT / "data/clips" / e["clip"]))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        fe = int(round(e["t"] * fps))
        f0 = max(int(round(e["t_attempt0"] * fps)), fe - int(WARM_S * fps))
        seq = []
        for fi in range(fe, f0 - 1, -STRIDE)[::-1]:       # ends exactly on the eval frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
            ok, fr = cap.read()
            if not ok:
                continue
            ka, sa = rtmo(fr, nms_thr=0.65, score_thr=0.3)
            kb, sb = v1(fr, nms_thr=0.65, score_thr=0.25)
            seq.append(dict(fi=fi, rtmo=(np.asarray(ka, np.float32).reshape(-1, 17, 2), np.asarray(sa, np.float32).reshape(-1, 17)),
                            v1=(kb, sb, v1.last_boxes.copy(), v1.last_box_scores.copy())))
            if fi == fe:
                cv2.imwrite(str(OUT / "frames" / f"r{e['row']:02d}_{e['pos']}.jpg"), fr, [cv2.IMWRITE_JPEG_QUALITY, 92])
        cap.release()
        e.update(fps=fps, fe=fe, seq=seq)
        cache.append(e)
        print(e["row"], e["pos"], len(seq), "frames", flush=True)
    name = "cache_neg.pkl" if neg else "cache.pkl"
    pickle.dump(cache, open(OUT / name, "wb"))
    print("wrote", OUT / name)


if __name__ == "__main__":
    main()
