"""Run the three models once per frame and cache raw outputs (local only, never upload).

    python -I research/referee/detector/cache_dets.py

Frames: every frame with i % 3 == 0 (tracking metrics, stride 3) or i % 5 == 0 (the
ref-appearance eval set uses stride 5). Per frame we store
  rtmo:  RTMO-m people at score 0.3 / nms 0.65 (as src/pose_smoke.py)
  fj:    fight-judge YOLOv8s fighter boxes (conf >= 0.10, NMS 0.5) and confidences
  td:    RTMPose-m (body7, 256x192) top-down keypoints on each fighter box with conf >= 0.25
plus per-model wall time. Output: data/referee/detector/cache/<clip>.pkl
"""
import glob
import pickle
import sys
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from fighter_boxes import FighterDetector  # noqa: E402

RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
RTMPOSE_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/"
             "rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.zip")
OUT = ROOT / "data" / "referee" / "detector"
TD_CONF = 0.25


def main():
    from rtmlib import RTMO, RTMPose
    rtmo = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    pose = RTMPose(onnx_model=RTMPOSE_M, model_input_size=(192, 256), backend="onnxruntime", device="cpu")
    det = FighterDetector(OUT / "weights" / "fight_judge_yolov8s.onnx", conf=0.10)
    (OUT / "cache").mkdir(parents=True, exist_ok=True)
    clips = sys.argv[1:] or sorted(glob.glob(str(ROOT / "data" / "clips" / "*.mp4")))
    for clip in clips:
        name = Path(clip).stem
        cap = cv2.VideoCapture(clip)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames, i = {}, 0
        while True:
            ok, img = cap.read()
            if not ok:
                break
            if i % 3 == 0 or i % 5 == 0:
                t0 = time.perf_counter()
                k, s = rtmo(img, nms_thr=0.65, score_thr=0.3)
                t1 = time.perf_counter()
                boxes, conf = det(img)
                t2 = time.perf_counter()
                tb = boxes[conf >= TD_CONF]
                if len(tb):
                    tk, ts = pose(img, bboxes=tb.tolist())
                else:
                    tk, ts = np.zeros((0, 17, 2), np.float32), np.zeros((0, 17), np.float32)
                t3 = time.perf_counter()
                frames[i] = {
                    "rtmo_k": np.asarray(k, np.float32).reshape(-1, 17, 2),
                    "rtmo_s": np.asarray(s, np.float32).reshape(-1, 17),
                    "fj_boxes": boxes, "fj_conf": conf,
                    "td_k": np.asarray(tk, np.float32).reshape(-1, 17, 2),
                    "td_s": np.asarray(ts, np.float32).reshape(-1, 17),
                    "t_rtmo": t1 - t0, "t_fj": t2 - t1, "t_td": t3 - t2, "n_td": len(tb),
                }
                if len(frames) % 100 == 0:
                    print(name, i, flush=True)
            i += 1
        cap.release()
        with open(OUT / "cache" / f"{name}.pkl", "wb") as fh:
            pickle.dump({"fps": fps, "n_frames": i, "frames": frames}, fh)
        print(name, "done", len(frames), "frames", flush=True)


if __name__ == "__main__":
    main()
