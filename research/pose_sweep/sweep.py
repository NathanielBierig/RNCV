"""Does RTMO lose the second fighter because of its own thresholds?

RTMO's defaults (score_thr 0.7, nms_thr 0.45) drop boxes that overlap another
box by IoU > 0.45, and entangled grapplers overlap heavily. This re-runs RTMO-m
on every k-th frame of data/clips/*.mp4 for a grid of thresholds and reports
how often 2+ people are found. Video stays local; only numbers are written.

    C:/Users/netan/.venvs/rncv/Scripts/python -I research/pose_sweep/sweep.py --every 15
"""
import argparse
import glob
import itertools
import json
import time
from pathlib import Path

import cv2
import numpy as np
from rtmlib import RTMO

ROOT = Path(__file__).resolve().parents[2]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")  # cached by src/pose_smoke.py
UPPER = [0, 5, 6, 7, 8, 9, 10]  # nose, shoulders, elbows, wrists


def frames(path, every):
    cap = cv2.VideoCapture(str(path))
    i = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % every == 0:
            yield fr
        i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=15)
    ap.add_argument("--score", type=float, nargs="*", default=[0.7, 0.5, 0.3])
    ap.add_argument("--nms", type=float, nargs="*", default=[0.45, 0.65, 0.85])
    ap.add_argument("--out", default=str(ROOT / "research/pose_sweep/results.json"))
    args = ap.parse_args()

    clips = sorted(glob.glob(str(ROOT / "data/clips/*.mp4")))
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    cache = {c: list(frames(c, args.every)) for c in clips}
    results = []
    for score, nms in itertools.product(args.score, args.nms):
        for c, frs in cache.items():
            t0, n2, n2up, ndet = time.time(), 0, 0, []
            for fr in frs:
                kpts, scores = model(fr, nms_thr=nms, score_thr=score)
                scores = np.asarray(scores).reshape(-1, 17) if len(scores) else np.zeros((0, 17))
                ndet.append(len(scores))
                n2 += len(scores) >= 2
                n2up += ((scores[:, UPPER] >= 0.3).sum(1) >= 5).sum() >= 2
            row = dict(clip=Path(c).stem, score_thr=score, nms_thr=nms, frames=len(frs),
                       pct_2plus_detections=100 * n2 / len(frs),
                       pct_2plus_upper_body_ok=100 * n2up / len(frs),
                       pct_3plus_detections=100 * np.mean(np.array(ndet) >= 3),
                       mean_detections=float(np.mean(ndet)), sec=round(time.time() - t0, 1))
            results.append(row)
            print(json.dumps(row), flush=True)
    Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
