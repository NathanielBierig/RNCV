"""Pose coverage inside each labeled RNC attempt -> reports/pose_attempts.md.

For every row of phase3_labels/labels.csv whose clip is in data/clips/ (`video_url`),
runs RTMO-m + two-fighter selection (referee filter) + tracking over the attempt window
[video_time_start, video_time_end] and reports, with the same measures as
reports/pose_smoke.md: % frames with both fighters tracked (seen, or filled <= 0.5 s)
and % frames where both upper bodies are OK (>= 5 of 7 upper-body joints).
Read-only on labels.csv.

    C:/Users/netan/.venvs/rncv/Scripts/python -I src/pose_attempts.py            # stride 2
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
import two_fighters as tf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
GATE = 60.0   # PLAN 2b gate: >= 60% usable frames during back control


def window_coverage(model, clip, t0, t1, stride, score_thr, nms_thr):
    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000)
    tracker = tf.TwoSlotTracker(fps / stride)
    n = both = upper = 0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok or cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 > t1:
            break
        if i % stride == 0:
            kps, scs = model(frame, nms_thr=nms_thr, score_thr=score_thr)
            kps = np.asarray(kps, np.float32).reshape(-1, 17, 2)
            scs = np.asarray(scs, np.float32).reshape(-1, 17)
            ks, ss, _, _ = tf.select(kps, scs, frame)
            poses, states = tracker.update(ks, ss)
            n += 1
            if all(s in (tf.SEEN, tf.FILLED) for s in states):
                both += 1
                upper += all(tf.upper_ok(poses[j, :, 2]) for j in range(2))
        i += 1
    cap.release()
    return n, 100 * both / max(n, 1), 100 * upper / max(n, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--score_thr", type=float, default=0.3)
    ap.add_argument("--nms_thr", type=float, default=0.65)
    args = ap.parse_args()
    labels = pd.read_csv(ROOT / "phase3_labels/labels.csv", dtype=str, keep_default_na=False)
    from rtmlib import RTMO
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    rows = []
    for k, r in labels.iterrows():
        clip = ROOT / "data/clips" / r.video_url
        if not r.video_url or not clip.exists():
            rows.append((k + 1, r.video_url or "—", r.outcome, "", "clip not found", "", ""))
            continue
        t0, t1 = float(r.video_time_start), float(r.video_time_end)
        n, both, upper = window_coverage(model, clip, t0, t1, args.stride, args.score_thr, args.nms_thr)
        flag = "🟢" if both >= GATE else "🔴"
        rows.append((k + 1, r.video_url, r.outcome, f"{t0:.1f}-{t1:.1f}", n, f"{flag} {both:.0f}%", f"{upper:.0f}%"))
        print(f"row {k + 1}: both tracked {both:.0f}%, upper OK {upper:.0f}%", flush=True)
    ok = [float(x[5].split()[1][:-1]) for x in rows if isinstance(x[4], int)]
    lines = ["# Pose coverage inside labeled attempts", "",
             f"RTMO-m (CPU), score {args.score_thr} / nms {args.nms_thr}, two-fighter selection with the referee filter, stride {args.stride}. "
             f"Gate (PLAN 2b): both fighters tracked in >= {GATE:.0f}% of frames.", "",
             "| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {' | '.join(str(x) for x in r)} |" for r in rows]
    if ok:
        lines += ["", f"Median both-tracked across {len(ok)} attempts: **{np.median(ok):.0f}%**; "
                      f"{sum(x >= GATE for x in ok)}/{len(ok)} attempts pass the gate."]
    lines += ["", "Re-run after the Kaggle fine-tune with the new model to compare (same command)."]
    (ROOT / "reports/pose_attempts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote reports/pose_attempts.md")


if __name__ == "__main__":
    main()
