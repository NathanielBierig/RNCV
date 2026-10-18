"""Render a submission-prediction overlay onto a recorded clip.

Usage:
    python overlay.py --video clip.mp4 --preds preds.csv --out clip_overlay.mp4

preds.csv columns (one row per prediction time, any rate):
    t_s        seconds from clip start
    sub_type   e.g. "RNC" (empty = no attempt detected -> panel hidden)
    prob       success probability 0..1
    factors    optional, ";"-separated top drivers, e.g. "+body triangle;-2-on-1 hand fight"
"""
import argparse

import cv2
import numpy as np
import pandas as pd

PANEL_W, PANEL_H = 360, 150
HISTORY_S = 8.0  # seconds of probability history in the sparkline


def prob_color(p):
    # BGR: red (low) -> yellow -> green (high)
    if p < 0.5:
        return (0, int(255 * p * 2), 255)
    return (0, 255, int(255 * (1 - p) * 2))


def load_preds(path):
    df = pd.read_csv(path).sort_values("t_s").reset_index(drop=True)
    df["sub_type"] = df["sub_type"].fillna("").astype(str)
    if "factors" not in df:
        df["factors"] = ""
    df["factors"] = df["factors"].fillna("").astype(str)
    return df


def pred_at(df, t):
    # Latest prediction at or before t (no peeking into the future).
    i = df["t_s"].searchsorted(t, side="right") - 1
    return None if i < 0 else df.iloc[i]


def draw_panel(frame, row, history, t):
    h, w = frame.shape[:2]
    x0, y0 = 20, h - PANEL_H - 20
    roi = frame[y0:y0 + PANEL_H, x0:x0 + PANEL_W]
    roi[:] = (roi * 0.35).astype(np.uint8)  # darkened translucent box

    p = float(row["prob"])
    col = prob_color(p)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, f"{row['sub_type']} ATTEMPT", (x0 + 12, y0 + 30), font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"{p * 100:.0f}%", (x0 + PANEL_W - 95, y0 + 32), font, 0.95, col, 2, cv2.LINE_AA)

    # Probability bar
    bx, by, bw, bh = x0 + 12, y0 + 44, PANEL_W - 24, 14
    cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (90, 90, 90), -1)
    cv2.rectangle(frame, (bx, by), (bx + int(bw * p), by + bh), col, -1)

    # Sparkline of recent probabilities
    sx, sy, sw, sh = bx, by + 24, bw, 34
    pts = [(sx + int(sw * (1 - (t - ht) / HISTORY_S)), sy + sh - int(sh * hp)) for ht, hp in history]
    if len(pts) > 1:
        cv2.polylines(frame, [np.array(pts, np.int32)], False, (220, 220, 220), 1, cv2.LINE_AA)

    # Top factors
    for k, f in enumerate([f for f in row["factors"].split(";") if f][:2]):
        fc = (120, 230, 120) if f.startswith("+") else (120, 120, 240)
        cv2.putText(frame, f, (bx, sy + sh + 18 + k * 18), font, 0.5, fc, 1, cv2.LINE_AA)


def render(video, preds, out):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    df = load_preds(preds)
    history, n = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = n / fps
        row = pred_at(df, t)
        if row is not None and row["sub_type"]:
            history.append((t, float(row["prob"])))
            history = [(ht, hp) for ht, hp in history if t - ht <= HISTORY_S]
            draw_panel(frame, row, history, t)
        else:
            history = []
        writer.write(frame)
        n += 1
    cap.release()
    writer.release()
    print(f"wrote {out} ({n} frames)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(a.video, a.preds, a.out)
