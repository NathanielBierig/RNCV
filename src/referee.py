"""Referee-vs-fighter appearance cues for one RTMO person (no model download needed).

UFC fighters are shirtless and wear shorts; the referee wears a black shirt, black
trousers and black gloves. So the share of *skin-coloured* pixels on the torso,
upper arms and legs separates them. Skin is detected by chroma (YCrCb Cr/Cb), not
brightness: dark skin keeps its red-orange chroma while black fabric is neutral
grey, which is why this does not repeat the "dark shirt" rule's failure on
Sterling. Pixels too dark to have a reliable colour are left out.

    referee_score(img, kpts, scores) -> float in [0, 1]   (1 = referee)

img: BGR frame (H, W, 3) uint8; kpts: [17, 2] pixel coords; scores: [17] joint conf.
Use it per detection, then average per track (see RESULTS.md, method 3c).
"""
import cv2
import numpy as np

THR = 0.3
TORSO = [(5, 6), (5, 11), (6, 12), (11, 12), (5, 12), (6, 11)]
UPPER_ARM = [(5, 7), (6, 8)]
LEGS = [(11, 13), (12, 14), (13, 15), (14, 16)]
DARK_Y = 30          # below this luma, colour is noise: pixel ignored
# Skin chroma box (OpenCV YCrCb, 8-bit), after Chai & Ngan 1999, Cr lower bound
# relaxed a bit for dim arena light on dark skin.
CR_MIN, CR_MAX, CB_MIN, CB_MAX = 135, 180, 77, 127


def _scale(k, s):
    p = k[s >= THR]
    if len(p) < 2:
        return 0.0
    w, h = p.max(0) - p.min(0)
    return float(max(w, h))


def region_mask(shape, k, s, pairs, width_frac=0.12):
    """Thick lines between confident joint pairs; None if no pair is confident."""
    sc = _scale(k, s)
    if sc <= 0:
        return None
    m = np.zeros(shape[:2], np.uint8)
    t = max(3, int(width_frac * sc))
    n = 0
    for a, b in pairs:
        if s[a] >= THR and s[b] >= THR:
            cv2.line(m, tuple(map(int, k[a])), tuple(map(int, k[b])), 255, t)
            n += 1
    return m if n else None


def skin_stats(ycc, mask):
    """(skin fraction among usable pixels, fraction of too-dark pixels, n pixels)."""
    if mask is None:
        return np.nan, np.nan, 0
    px = ycc[mask > 0]
    if len(px) < 30:
        return np.nan, np.nan, len(px)
    y, cr, cb = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
    lit = y >= DARK_Y
    dark = 1.0 - lit.mean()
    if lit.sum() < 15:
        return np.nan, dark, len(px)
    skin = (cr >= CR_MIN) & (cr <= CR_MAX) & (cb >= CB_MIN) & (cb <= CB_MAX)
    return float(skin[lit].mean()), float(dark), len(px)


def clothing_features(img, kpts, scores):
    """Dict of skin fractions for torso / upper arms / legs (NaN = not visible)."""
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    out = {}
    for name, pairs in (("torso", TORSO), ("uarm", UPPER_ARM), ("legs", LEGS)):
        f, d, n = skin_stats(ycc, region_mask(img.shape, kpts, scores, pairs))
        out[f"{name}_skin"], out[f"{name}_dark"], out[f"{name}_n"] = f, d, n
    return out


DARK_W = 0.5         # a too-dark pixel counts as half a "not skin" pixel (black shirt = mostly too dark)


def referee_score(img, kpts, scores, dark_w=DARK_W):
    """1 - skin share over torso, upper arms and legs, where too-dark pixels count dark_w as 'not skin'.

    Ignoring dark pixels (dark_w=0, the old rule) let a black-shirted referee be judged on the few lit
    pixels (bare forearm, highlights), giving him 0.2-0.3 on attempt frames. With 0.5: AUC 0.92 -> 0.99 on
    research/referee/eval (research/pose_review/ref_dark.py). Use threshold 0.6.
    0.5 when nothing usable is visible (unknown).
    """
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    k, s = np.asarray(kpts, float), np.asarray(scores, float)
    num = den = 0.0
    for pairs in (TORSO, UPPER_ARM, LEGS):
        m = region_mask(img.shape, k, s, pairs)
        if m is None:
            continue
        px = ycc[m > 0]
        if len(px) < 30:
            continue
        y, cr, cb = px[:, 0].astype(int), px[:, 1].astype(int), px[:, 2].astype(int)
        lit = y >= DARK_Y
        skin = lit & (cr >= CR_MIN) & (cr <= CR_MAX) & (cb >= CB_MIN) & (cb <= CB_MAX)
        num += skin.sum()
        den += lit.sum() + dark_w * (~lit).sum()
    return 0.5 if den == 0 else float(1 - num / den)
