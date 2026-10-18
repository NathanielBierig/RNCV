"""Phase 2b smoke test: run RTMO-m pose on UFC clips with the laptop CPU.

For every clip it saves keypoints, a skeleton-overlay preview (local only, under
data/ which is gitignored) and a row in reports/pose_smoke.md with CPU fps and
how often two people get >= 12 confident joints.

    C:/Users/netan/.venvs/rncv/Scripts/python -I src/pose_smoke.py
    C:/Users/netan/.venvs/rncv/Scripts/python -I src/pose_smoke.py --clips tools/overlay/demo_clip.mp4 --stride 1

Outputs per clip <name>:
    data/pose/<name>.npz           kpts [F, P, 17, 3] (x, y, conf; NaN padded), frame_idx, fps, stride
    data/pose/<name>_preview.mp4   skeletons drawn on the processed frames
Caveat: the referee is a person too. "2 people with >= 12 joints" can count the
ref instead of a fighter, so check the previews by eye before trusting it.
"""
import argparse
import glob
import platform
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
MAX_PEOPLE = 4
SKELETON = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
COLORS = [(0, 200, 255), (255, 120, 0), (0, 255, 0), (200, 0, 200)]


def rank_people(kpts, scores, thr):
    """Order detections by (#confident joints, mean conf); return indices."""
    good = (scores >= thr).sum(1)
    return np.lexsort((-scores.mean(1), -good))


def draw(frame, people, thr):
    for p, kp in enumerate(people):
        col = COLORS[p % len(COLORS)]
        ok = kp[:, 2] >= thr
        for a, b in SKELETON:
            if ok[a] and ok[b]:
                cv2.line(frame, tuple(map(int, kp[a, :2])), tuple(map(int, kp[b, :2])), col, 2)
        for j in np.where(ok)[0]:
            cv2.circle(frame, tuple(map(int, kp[j, :2])), 3, col, -1)
    return frame


def run_clip(path, model, args):
    name = Path(path).stem
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_dir = ROOT / "data" / "pose"
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = None
    kpts_all, idx_all, infer_s = [], [], []
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok or (args.max_frames and len(idx_all) >= args.max_frames):
            break
        if i % args.stride == 0:
            t0 = time.perf_counter()
            kps, scs = model(frame)
            infer_s.append(time.perf_counter() - t0)
            kps = np.asarray(kps, dtype=np.float32).reshape(-1, 17, 2)
            scs = np.asarray(scs, dtype=np.float32).reshape(-1, 17)
            people = np.full((MAX_PEOPLE, 17, 3), np.nan, dtype=np.float32)
            for slot, d in enumerate(rank_people(kps, scs, args.kpt_thr)[:MAX_PEOPLE] if len(kps) else []):
                people[slot, :, :2] = kps[d]
                people[slot, :, 2] = scs[d]
            kpts_all.append(people); idx_all.append(i)
            if not args.no_preview:
                if writer is None:
                    h, w = frame.shape[:2]
                    writer = cv2.VideoWriter(str(out_dir / f"{name}_preview.mp4"),
                                             cv2.VideoWriter_fourcc(*"mp4v"), fps / args.stride, (w, h))
                shown = [p for p in people if not np.isnan(p[0, 0])]
                writer.write(draw(frame, shown, args.kpt_thr))
        i += 1
    cap.release()
    if writer is not None:
        writer.release()
    if not idx_all:
        raise SystemExit(f"no frames read from {path}")

    kpts = np.stack(kpts_all)
    np.savez_compressed(out_dir / f"{name}.npz", kpts=kpts, frame_idx=np.array(idx_all),
                        fps=fps, stride=args.stride, kpt_thr=args.kpt_thr)
    good = (np.nan_to_num(kpts[..., 2]) >= args.kpt_thr).sum(-1)   # [F, P] confident joints
    n_good = (good >= args.min_joints).sum(1)                       # people per frame passing
    warm = infer_s[1:] or infer_s                                    # first call includes warm-up
    return {
        "clip": name, "frames_in_clip": n_total, "frames_processed": len(idx_all),
        "stride": args.stride, "cpu_fps": 1.0 / np.mean(warm),
        "pct_two_people": 100 * (n_good >= 2).mean(),
        "pct_one_plus": 100 * (n_good >= 1).mean(),
        "pct_three_plus": 100 * (n_good >= 3).mean(),
        "mean_detections": float((good >= 1).sum(1).mean()),        # people with >= 1 confident joint
    }


def write_report(rows, args):
    lines = [
        "# Pose smoke test (Phase 2b)", "",
        f"Model: RTMO-m (rtmlib + onnxruntime, CPU). Machine: {platform.processor() or platform.machine()}. "
        f"Joint counted as confident if score >= {args.kpt_thr}; a person 'passes' with >= {args.min_joints} of 17.", "",
        "| Clip | Frames processed (stride) | CPU fps | % frames 2+ people pass | 1+ | 3+ (ref visible?) | Mean people (>= 1 confident joint) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['clip']} | {r['frames_processed']} of {r['frames_in_clip']} ({r['stride']}) | "
                     f"{r['cpu_fps']:.2f} | {r['pct_two_people']:.1f}% | {r['pct_one_plus']:.1f}% | "
                     f"{r['pct_three_plus']:.1f}% | {r['mean_detections']:.2f} |")
    lines += ["",
              "**How to read it:** '2+ people pass' is an upper bound on 'both fighters tracked', since the referee can be one of the two.",
              "Open `data/pose/<clip>_preview.mp4` and check that the skeletons sit on the fighters during the RNC.",
              f"At {np.mean([r['cpu_fps'] for r in rows]):.1f} fps, a 60 s clip at 30 fps with stride 3 takes about "
              f"{600 / max(np.mean([r['cpu_fps'] for r in rows]), 1e-6) / 60:.0f} min on this CPU."]
    out = ROOT / "reports" / "pose_smoke.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs="*", help="video files (default: data/clips/*.mp4)")
    ap.add_argument("--stride", type=int, default=3, help="process every k-th frame (CPU is slow)")
    ap.add_argument("--max-frames", type=int, default=0, help="stop each clip after this many processed frames")
    ap.add_argument("--kpt-thr", type=float, default=0.3)
    ap.add_argument("--min-joints", type=int, default=12)
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args()

    clips = args.clips or sorted(glob.glob(str(ROOT / "data" / "clips" / "*.mp4")))
    if not clips:
        raise SystemExit("No clips found. Put .mp4 files in data/clips/ or pass --clips path.mp4")

    from rtmlib import RTMO
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    rows = []
    for c in clips:
        print(f"-> {c}")
        rows.append(run_clip(c, model, args))
        print(rows[-1])
    write_report(rows, args)


if __name__ == "__main__":
    main()
