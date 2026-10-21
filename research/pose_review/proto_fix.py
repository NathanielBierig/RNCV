"""Prototype fixes, scored on the correctness eval (render.py --extra proto_fix:pipe_D,...).

D = C with referee_score_dark(): too-dark pixels count as half 'not skin' (a black shirt is mostly
    too dark, and src/referee.py ignores those pixels), threshold 0.6.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from common import tf  # noqa: E402
import referee as R  # noqa: E402

DARK_W, REF_THR = 0.5, 0.6


def referee_score_dark(img, kpts, scores, dark_w=DARK_W):
    """Like referee.referee_score, but too-dark pixels count as dark_w 'not skin' instead of being ignored."""
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    k, s = np.asarray(kpts, float), np.asarray(scores, float)
    num = den = 0.0
    for pairs in (R.TORSO, R.UPPER_ARM, R.LEGS):
        m = R.region_mask(img.shape, k, s, pairs)
        if m is None:
            continue
        px = ycc[m > 0]
        if len(px) < 30:
            continue
        y, cr, cb = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
        lit = y >= R.DARK_Y
        skin = (cr >= R.CR_MIN) & (cr <= R.CR_MAX) & (cb >= R.CB_MIN) & (cb <= R.CB_MAX) & lit
        num += skin.sum()
        den += lit.sum() + dark_w * (~lit).sum()
    return 0.5 if den == 0 else float(1 - num / den)


class _patched:
    """Temporarily swap the referee function/threshold used inside two_fighters.select."""
    def __init__(self, fn, thr):
        self.fn, self.thr = fn, thr

    def __enter__(self):
        self.old = tf.referee_score, tf.REF_THR
        tf.referee_score, tf.REF_THR = self.fn, self.thr

    def __exit__(self, *a):
        tf.referee_score, tf.REF_THR = self.old


def pipe_D(e, frames):
    with _patched(referee_score_dark, REF_THR):
        return common.pipe_C(e, frames)


def no_ref_fill(e, frames, kept, thr=REF_THR):
    """E: replay + drop a FILLED slot whose stale pose now looks like the referee (dark-aware score)."""
    poses, states = common.replay(e, kept)
    img = frames[-1]
    for j in range(2):
        if states[j] == tf.FILLED and referee_score_dark(img, poses[j, :, :2], np.nan_to_num(poses[j, :, 2])) > thr:
            states[j] = tf.MISSING
    return poses, states
