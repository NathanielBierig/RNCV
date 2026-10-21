"""Shared helpers for the pose correctness eval: load the cache, replay pipelines, draw panels.

A pipeline = a function (entry, frames) -> per processed frame list of (kpts [n,17,2], scores [n,17]).
replay() feeds it through the real TwoSlotTracker and returns the tracked poses at the eval frame.
"""
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402
from referee import referee_score  # noqa: E402

OUT = ROOT / "data/pose_review"
SKEL = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
        (0, 5), (0, 6)]


def load_cache():
    return pickle.load(open(OUT / "cache.pkl", "rb"))


def read_frames(e):
    """BGR frames for every cached frame index of an entry (sequential read)."""
    cap = cv2.VideoCapture(str(ROOT / "data/clips" / e["clip"]))
    want = [s["fi"] for s in e["seq"]]
    cap.set(cv2.CAP_PROP_POS_FRAMES, want[0])
    fi, out = want[0], {}
    while fi <= want[-1]:
        ok, fr = cap.read()
        if not ok:
            break
        if fi in want:
            out[fi] = fr
        fi += 1
    cap.release()
    return [out.get(s["fi"]) for s in e["seq"]]


def sel(k, s, img):
    ks, ss, _, _ = tf.select(np.asarray(k, np.float32).reshape(-1, 17, 2), np.asarray(s, np.float32).reshape(-1, 17), img)
    return ks, ss


def pipe_A(e, frames):
    return [sel(*s["rtmo"], f) for s, f in zip(e["seq"], frames)]


def pipe_B(e, frames):
    return [sel(s["v1"][0], s["v1"][1], f) for s, f in zip(e["seq"], frames)]


def pipe_C(e, frames):
    out = []
    for s, f in zip(e["seq"], frames):
        ks, ss = sel(s["v1"][0], s["v1"][1], f)
        if len(ks) < 2:
            k2, s2 = sel(*s["rtmo"], f)
            if len(k2) > len(ks):
                ks, ss = k2, s2
        out.append((ks, ss))
    return out


def replay(e, kept, max_gap_s=0.5):
    """Run TwoSlotTracker over the per-frame kept people -> (poses [2,17,3], states [2]) at the eval frame."""
    tr = tf.TwoSlotTracker(e["fps"] / 2, max_gap_s)
    poses = states = None
    for ks, ss in kept:
        poses, states = tr.update(ks, ss)
    return poses, states


COL = [(0, 165, 255), (255, 255, 0)]    # slot 0 orange, slot 1 cyan (BGR)


def draw(img, poses, states, extra=(), title=""):
    """Slots coloured, joints >= 0.3 solid; `extra` = list of (kpts, scores) drawn thin grey (dropped)."""
    im = img.copy()
    sc = max(2, img.shape[1] // 500)
    for k, s in extra:
        for a, b in SKEL:
            if s[a] >= tf.THR and s[b] >= tf.THR:
                cv2.line(im, tuple(map(int, k[a])), tuple(map(int, k[b])), (150, 150, 150), max(1, sc // 2), cv2.LINE_AA)
    for j in range(2):
        if states is None or states[j] == tf.MISSING:
            continue
        k, s = poses[j, :, :2], poses[j, :, 2]
        for a, b in SKEL:
            if s[a] >= tf.THR and s[b] >= tf.THR:
                cv2.line(im, tuple(map(int, k[a])), tuple(map(int, k[b])), COL[j], sc + 1, cv2.LINE_AA)
        for q in range(17):
            if s[q] >= tf.THR:
                cv2.circle(im, tuple(map(int, k[q])), sc + 3, COL[j], -1, cv2.LINE_AA)
        if s[0] >= tf.THR:   # nose marked white
            cv2.circle(im, tuple(map(int, k[0])), sc + 4, (255, 255, 255), 2, cv2.LINE_AA)
    return im


def crop_box(img_shape, people, margin=0.12):
    """Union box of all people's confident joints (+margin), at least 40% of the frame width."""
    H, W = img_shape[:2]
    pts = [k[s >= tf.THR] for k, s in people if (s >= tf.THR).sum() >= 3]
    if not pts:
        return 0, 0, W, H
    p = np.concatenate(pts)
    x0, y0 = p.min(0)
    x1, y1 = p.max(0)
    mw, mh = margin * (x1 - x0) + 20, margin * (y1 - y0) + 20
    x0, x1, y0, y1 = max(0, x0 - mw), min(W, x1 + mw), max(0, y0 - mh), min(H, y1 + mh)
    if x1 - x0 < 0.4 * W:
        c = (x0 + x1) / 2
        x0, x1 = max(0, c - 0.2 * W), min(W, c + 0.2 * W)
    if y1 - y0 < 0.4 * H:
        c = (y0 + y1) / 2
        y0, y1 = max(0, c - 0.2 * H), min(H, c + 0.2 * H)
    return int(x0), int(y0), int(x1), int(y1)
