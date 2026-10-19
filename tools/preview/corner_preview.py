"""Red/blue corner preview: both fighters colored by corner, with scores on screen.

Runs RTMO-m (low threshold, per research/pose_sweep/FINDINGS.md), keeps the two
fighters with src/two_fighters.py, and guesses each fighter's corner from the
colors near their wrists (gloves) and hips (trunks). Draws:
  - each fighter's skeleton in red or blue, with a label: corner, pose score %,
    seen/filled state, and whether the corner color was confirmed or guessed
  - people dropped as crowd/referee/duplicate in thin gray
  - a top bar: clip time, live "both fighters tracked" %, and the frame's state

    C:/Users/netan/.venvs/rncv/Scripts/python -I tools/preview/corner_preview.py
    C:/Users/netan/.venvs/rncv/Scripts/python -I tools/preview/corner_preview.py --clips data/clips/gsp_bisping.mp4 --stride 1

Output: data/pose/<clip>_corners.mp4 (local only; data/ is gitignored).
Caveat: modern UFC gloves are mostly black, so the glove signal is often weak;
the corner is then a guess and is labeled "?" until enough color evidence builds up.
"""
import argparse
import glob
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from two_fighters import FILLED, SEEN, THR, TwoSlotTracker, select, upper_ok  # noqa: E402

RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
SKELETON = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
RED, BLUE, GRAY = (40, 40, 230), (230, 120, 30), (150, 150, 150)
COLOR_JOINTS = [9, 10, 11, 12]          # wrists (gloves) and hips (trunks)
MIN_EVIDENCE = 400                       # colored pixels needed before a corner counts as confirmed


def color_votes(img, k, s):
    """(red_px, blue_px) in small patches around wrists and hips."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    pts = k[s >= THR]
    scale = max(np.ptp(pts[:, 1]) if len(pts) > 2 else 0, 40)
    r = int(max(6, 0.05 * scale))
    red = blue = 0
    for j in COLOR_JOINTS:
        if s[j] < THR:
            continue
        x, y = int(k[j, 0]), int(k[j, 1])
        patch = hsv[max(0, y - r):y + r, max(0, x - r):x + r]
        if patch.size == 0:
            continue
        h, sat, v = patch[..., 0], patch[..., 1], patch[..., 2]
        # Strict hues: skin tones (hue ~5-20) and the mat's logos otherwise read as "red".
        strong = (sat > 160) & (v > 80)
        red += int((strong & ((h < 4) | (h > 176))).sum())
        blue += int((strong & (h > 104) & (h < 126)).sum())
    return red, blue


def draw_person(img, k, s, color, thick):
    for a, b in SKELETON:
        if s[a] >= THR and s[b] >= THR:
            cv2.line(img, tuple(map(int, k[a])), tuple(map(int, k[b])), color, thick, cv2.LINE_AA)
    for j in range(17):
        if s[j] >= THR:
            cv2.circle(img, tuple(map(int, k[j])), thick + 1, color, -1, cv2.LINE_AA)


def label(img, text, org, color):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    x, y = int(org[0]), int(max(h + 8, org[1]))
    cv2.rectangle(img, (x - 4, y - h - 8), (x + w + 4, y + 6), color, -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)


def run_clip(path, model, args):
    name = Path(path).stem
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = ROOT / "data" / "pose" / f"{name}_corners.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps / args.stride, (w, h))
    tracker = TwoSlotTracker(fps / args.stride)
    votes = np.zeros((2, 2))             # slot x (red, blue) cumulative colored pixels
    both, n, i = 0, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % args.stride:
            i += 1
            continue
        kps, scs = model(frame, nms_thr=args.nms, score_thr=args.score)
        kps = np.asarray(kps, np.float32).reshape(-1, 17, 2)
        scs = np.asarray(scs, np.float32).reshape(-1, 17)
        ks, ss, dropped, _ = select(kps, scs, frame)
        poses, states = tracker.update(ks, ss)
        for k in dropped:
            draw_person(frame, k, np.ones(17), GRAY, 1)
        for j in range(2):
            if states[j] == SEEN:
                votes[j] += color_votes(frame, poses[j, :, :2], poses[j, :, 2])
        # Corner per slot: the slot with the stronger red-vs-blue lean gets its color, the other the opposite.
        lean = (votes[:, 0] - votes[:, 1]) / (votes.sum(1) + 1)
        red_slot = int(np.argmax(lean)) if abs(lean[0] - lean[1]) > 0 else 0
        confirmed = votes.sum() >= MIN_EVIDENCE and abs(lean[0] - lean[1]) > 0.2
        n += 1
        both += int(all(st in (SEEN, FILLED) for st in states))
        for j in range(2):
            if states[j] == 0:
                continue
            k, s = poses[j, :, :2], poses[j, :, 2]
            is_red = j == red_slot
            col = RED if is_red else BLUE
            draw_person(frame, k, s, col, 4 if states[j] == SEEN else 2)
            vis = s[s >= THR]
            score = 100 * float(vis.mean()) if len(vis) else 0
            tag = ("RED" if is_red else "BLUE") + ("" if confirmed else " ?")
            state = "seen" if states[j] == SEEN else "filled"
            body = "" if upper_ok(s) else " | upper body weak"
            top = k[s >= THR][:, 1].argmin() if (s >= THR).any() else 0
            anchor = k[s >= THR][top] if (s >= THR).any() else k[0]
            label(frame, f"{tag}  pose {score:.0f}%  {state}{body}", (anchor[0] - 60, anchor[1] - 25), col)
        hud = (f"{name}  t={i / fps:5.1f}s   both fighters tracked: {100 * both / n:4.0f}%   "
               f"corners: {'confirmed by color' if confirmed else 'guessed (gloves/trunks unclear)'}")
        cv2.rectangle(frame, (0, 0), (w, 44), (20, 20, 20), -1)
        cv2.putText(frame, hud, (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        writer.write(frame)
        i += 1
    cap.release()
    writer.release()
    print(f"{name}: wrote {out.relative_to(ROOT)} | both tracked {100 * both / max(n, 1):.0f}% of "
          f"{n} frames | corners {'confirmed' if confirmed else 'guessed'} (red/blue px per slot: {votes.astype(int).tolist()})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", nargs="*", default=sorted(glob.glob(str(ROOT / "data" / "clips" / "*.mp4"))))
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--score", type=float, default=0.3)
    ap.add_argument("--nms", type=float, default=0.65)
    args = ap.parse_args()
    from rtmlib import RTMO
    model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
    for p in args.clips:
        run_clip(p, model, args)


if __name__ == "__main__":
    main()
