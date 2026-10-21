"""Phase 2b smoke test: RTMO-m pose + two-fighter selection on UFC clips (laptop CPU).

Pipeline per processed frame (research/pose_sweep/FINDINGS.md has the evidence):
  RTMO-m at score_thr 0.3 / nms_thr 0.65 (the 0.7 default drops the tangled
  second fighter) -> src/two_fighters.select (drop crowd, duplicates; with 3+
  people keep the most-overlapping pair) -> 2-slot tracker that fills a missing
  fighter for up to 0.5 s.

    C:/Users/netan/.venvs/rncv/Scripts/python -I src/pose_smoke.py
    C:/Users/netan/.venvs/rncv/Scripts/python -I src/pose_smoke.py --clips data/clips/gsp_bisping.mp4 --stride 1

Outputs per clip <name> (local only, data/ is gitignored):
    data/pose/<name>.npz           kpts [F, 2, 17, 3] tracked fighters (x, y, conf; NaN = missing),
                                   state [F, 2] (0 missing, 1 seen, 2 filled), raw_people, frame_idx, ...
    data/pose/<name>_preview.mp4   orange/cyan = fighter slots (thin = filled), red dots = dropped people
Results go to the top of reports/pose_smoke.md; hand-written "## " sections there are kept.
Caveat: referee removal is NOT solved. The overlap rule sometimes keeps the
referee and drops a fighter, so check previews by eye before trusting the numbers.
"""
import argparse
import glob
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

import cv2
import numpy as np

import two_fighters as tf

ROOT = Path(__file__).resolve().parents[1]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
SKELETON = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
SLOT_COLORS = [(0, 165, 255), (255, 200, 0)]      # BGR: orange, cyan
STATE_NAMES = ["missing", "seen", "filled"]


def draw(frame, poses, states, dropped, thr):
    for kp in dropped:
        for x, y in kp.astype(int):
            cv2.circle(frame, (int(x), int(y)), 4, (0, 0, 255), -1)
    for slot, (kp, st) in enumerate(zip(poses, states)):
        if st == tf.MISSING:
            continue
        col, width = SLOT_COLORS[slot], 2 if st == tf.SEEN else 1
        ok = kp[:, 2] >= thr
        for a, b in SKELETON:
            if ok[a] and ok[b]:
                cv2.line(frame, tuple(map(int, kp[a, :2])), tuple(map(int, kp[b, :2])), col, width)
        for j in np.where(ok)[0]:
            cv2.circle(frame, tuple(map(int, kp[j, :2])), 3, col, -1)
    label = " ".join(f"F{j + 1}:{STATE_NAMES[st]}" for j, st in enumerate(states))
    cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
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
    tracker = tf.TwoSlotTracker(fps / args.stride, args.max_gap)
    writer = None
    kpts_all, state_all, raw_n, sel_joints, sel_upper, idx_all, infer_s = [], [], [], [], [], [], []
    drops = {"crowd": 0, "dup": 0, "ref_look": 0, "ref": 0, "junk": 0}
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok or (args.max_frames and len(idx_all) >= args.max_frames):
            break
        if i % args.stride == 0:
            t0 = time.perf_counter()
            kps, scs = model(frame, nms_thr=args.nms_thr, score_thr=args.score_thr)
            infer_s.append(time.perf_counter() - t0)
            kps = np.asarray(kps, dtype=np.float32).reshape(-1, 17, 2)
            scs = np.asarray(scs, dtype=np.float32).reshape(-1, 17)
            ks, ss, dropped, counts = tf.select(kps, scs, frame)
            for key in drops:
                drops[key] += counts[key]
            poses, states = tracker.update(ks, ss)
            raw_n.append(len(scs))
            sel_joints.append(len(ss) == 2 and all((s >= args.kpt_thr).sum() >= args.min_joints for s in ss))
            sel_upper.append(len(ss) == 2 and all(tf.upper_ok(s) for s in ss))
            kpts_all.append(poses); state_all.append(states); idx_all.append(i)
            if not args.no_preview:
                if writer is None:
                    h, w = frame.shape[:2]
                    writer = cv2.VideoWriter(str(out_dir / f"{name}_preview.mp4"),
                                             cv2.VideoWriter_fourcc(*"mp4v"), fps / args.stride, (w, h))
                writer.write(draw(frame, poses, states, dropped, args.kpt_thr))
        i += 1
    cap.release()
    if writer is not None:
        writer.release()
    if not idx_all:
        raise SystemExit(f"no frames read from {path}")

    state = np.stack(state_all)
    raw_n = np.array(raw_n)
    np.savez_compressed(out_dir / f"{name}.npz", kpts=np.stack(kpts_all), state=state, raw_people=raw_n,
                        frame_idx=np.array(idx_all), fps=fps, stride=args.stride, score_thr=args.score_thr,
                        nms_thr=args.nms_thr, max_gap_s=args.max_gap, kpt_thr=args.kpt_thr)
    warm = infer_s[1:] or infer_s                                    # first call includes warm-up
    return {
        "clip": name, "frames_in_clip": n_total, "frames_processed": len(idx_all),
        "stride": args.stride, "cpu_fps": 1.0 / np.mean(warm),
        "pct_raw_2plus": 100 * (raw_n >= 2).mean(),
        "pct_2_selected_min_joints": 100 * np.mean(sel_joints),
        "pct_2_selected_upper_ok": 100 * np.mean(sel_upper),
        "pct_2_seen": 100 * (state == tf.SEEN).all(1).mean(),
        "pct_2_seen_or_filled": 100 * (state != tf.MISSING).all(1).mean(),
        "dropped": drops,
    }


def write_report(rows, args):
    lines = [
        "# Pose smoke test (Phase 2b)", "",
        f"Latest run of `src/pose_smoke.py`. Model: RTMO-m (rtmlib + onnxruntime, CPU), score_thr {args.score_thr}, "
        f"nms_thr {args.nms_thr}, then two-fighter selection + 2-slot tracking with gap fill up to {args.max_gap} s. "
        f"Machine: {platform.processor() or platform.machine()}.", "",
        f"| Clip | Frames processed (stride) | CPU fps | 2+ raw detections | 2 fighters kept, both >= {args.min_joints}/17 joints "
        "| 2 kept, both upper bodies OK | 2 tracked (seen) | 2 tracked (seen or filled) | Dropped crowd / dup / ref |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        d = r["dropped"]
        lines.append(f"| {r['clip']} | {r['frames_processed']} of {r['frames_in_clip']} ({r['stride']}) | "
                     f"{r['cpu_fps']:.2f} | {r['pct_raw_2plus']:.0f}% | {r['pct_2_selected_min_joints']:.0f}% | "
                     f"{r['pct_2_selected_upper_ok']:.0f}% | {r['pct_2_seen']:.0f}% | {r['pct_2_seen_or_filled']:.0f}% | "
                     f"{d['crowd']} / {d['dup']} / {d['ref']} |")
    lines += ["",
              '**How to read it:** "kept" and "tracked" are upper bounds on *fighter* coverage. Referee removal is not '
              "solved, so some kept people are the referee. Open `data/pose/<clip>_preview.mp4` (orange/cyan = fighter "
              "slots, thin = filled from the last pose, red dots = dropped people) and check by eye.",
              "Upper body OK = at least 5 of 7 upper-body joints (nose, shoulders, elbows, wrists) confident, "
              "which is what an RNC needs.",
              "Before this change (RTMO defaults 0.7 / 0.45, no selection), the >= 12/17 column was 23% / 0% / 1% "
              "for gsp_bisping / pantoja_asakura_r2 / sterling_sandhagen (see the notes below)."]
    out = ROOT / "reports" / "pose_smoke.md"
    out.parent.mkdir(exist_ok=True)
    kept = ""
    if out.exists():                       # keep hand-written "## " sections from earlier runs
        old = out.read_text(encoding="utf-8")
        pos = old.find("\n## ")
        kept = old[pos:] if pos >= 0 else ""
    out.write_text("\n".join(lines) + "\n" + kept, encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs="*", help="video files (default: data/clips/*.mp4)")
    ap.add_argument("--stride", type=int, default=3, help="process every k-th frame (CPU is slow)")
    ap.add_argument("--max-frames", type=int, default=0, help="stop each clip after this many processed frames")
    ap.add_argument("--score-thr", type=float, default=0.3, help="RTMO person score cutoff (rtmlib default 0.7)")
    ap.add_argument("--nms-thr", type=float, default=0.65, help="RTMO box overlap cutoff (rtmlib default 0.45)")
    ap.add_argument("--max-gap", type=float, default=0.5, help="seconds a lost fighter is filled from its last pose")
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
