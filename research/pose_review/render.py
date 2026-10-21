"""Render grading sheets: one sheet per labeled attempt, 3 rows (start / mid / end), 4 panels per row:
clean crop | A RTMO-m 0.3/0.65 | B fine-tuned v1 0.25 | C = B + RTMO fallback (pose_attempts.detect).
Kept/tracked slot 0 = orange, slot 1 = cyan (nose ringed white); grey = raw detections not kept.
Each panel's caption: slot states (S seen, F filled, - missing) and referee_score per slot.

    C:/Users/netan/.venvs/rncv/Scripts/python -I research/pose_review/render.py [--pipes A,B,C] [--extra mod:func]
Outputs data/pose_review/sheets/rowNN.jpg and data/pose_review/tracked_<pipe>.pkl.
"""
import argparse
import importlib
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from common import OUT, crop_box, draw, load_cache, pipe_A, pipe_B, pipe_C, read_frames, referee_score, replay, tf  # noqa: E402

PH = 280


def caption(im, txt):
    cv2.rectangle(im, (0, 0), (im.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(im, txt, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipes", default="A,B,C")
    ap.add_argument("--extra", default="", help="module:function of an extra pipeline (e.g. proto_fix:pipe_D)")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    pipes = {"A": pipe_A, "B": pipe_B, "C": pipe_C}
    pipes = {p: pipes[p] for p in args.pipes.split(",") if p}
    if args.extra:
        for spec in args.extra.split(","):
            m, f = spec.split(":")
            pipes[f.replace("pipe_", "")] = getattr(importlib.import_module(m), f)
    cache = load_cache()
    tracked = {p: {} for p in pipes}
    rows = {}
    for e in cache:
        frames = read_frames(e)
        img = frames[-1]
        last = e["seq"][-1]
        raw = list(zip(*last["rtmo"])) + list(zip(last["v1"][0], last["v1"][1]))
        panels = []
        res = {}
        for p, fn in pipes.items():
            poses, states = replay(e, fn(e, frames))
            res[p] = (poses, states)
            tracked[p][(e["row"], e["pos"])] = (poses, states)
        people = raw + [(r[0][j, :, :2], np.nan_to_num(r[0][j, :, 2])) for r in res.values() for j in range(2) if r[1][j]]
        x0, y0, x1, y1 = crop_box(img.shape, people)
        sc = PH / (y1 - y0)
        size = (int((x1 - x0) * sc), PH)
        panels.append(caption(cv2.resize(img[y0:y1, x0:x1], size), f"row {e['row']} {e['pos']} {e['context']} t={e['t']:.1f}"))
        for p, (poses, states) in res.items():
            src = last["rtmo"] if p == "A" else (last["v1"][0], last["v1"][1])
            im = draw(img, poses, states, extra=list(zip(*src)))
            refs = []
            for j in range(2):
                if states[j]:
                    refs.append(f"{'SF'[states[j] - 1]}{referee_score(img, poses[j, :, :2], poses[j, :, 2]):.2f}")
                else:
                    refs.append("-")
            panels.append(caption(cv2.resize(im[y0:y1, x0:x1], size), f"{p}  {' '.join(refs)}"))
        rows.setdefault(e["row"], []).append(np.hstack(panels))
        print(e["row"], e["pos"], flush=True)
    (OUT / f"sheets{args.tag}").mkdir(exist_ok=True)
    for r, ims in rows.items():
        w = max(i.shape[1] for i in ims)
        ims = [cv2.copyMakeBorder(i, 0, 4, 0, w - i.shape[1], cv2.BORDER_CONSTANT, value=(40, 40, 40)) for i in ims]
        cv2.imwrite(str(OUT / f"sheets{args.tag}" / f"row{r:02d}.jpg"), np.vstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 85])
    for p, d in tracked.items():
        pickle.dump(d, open(OUT / f"tracked_{p}.pkl", "wb"))


if __name__ == "__main__":
    main()
