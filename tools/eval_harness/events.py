"""Phase 4: turn window probabilities into attempt segments and score them.

A predicted segment is a hit if its temporal IoU with an unmatched true
attempt in the same fight is >= iou_thr (greedy, highest score first).
"""
import numpy as np
import pandas as pd


def segments_from_probs(t, p, on=0.6, off=0.4, min_len=1.5, resets=()):
    """Hysteresis thresholding. t, p: 1-D arrays (seconds, probability).

    `resets` are times (e.g. scene cuts) where an open segment is closed.
    Returns a DataFrame with start_s, end_s, score (max p inside).
    """
    t, p = np.asarray(t, float), np.asarray(p, float)
    resets = np.sort(np.asarray(resets, float))
    segs, start, peak = [], None, 0.0
    for i in range(len(t)):
        cut = start is not None and np.any((resets > t[start]) & (resets <= t[i]))
        if start is not None and (p[i] < off or cut):
            segs.append((t[start], t[i - 1] if i > 0 else t[i], peak))
            start = None
        if start is None and p[i] >= on:
            start, peak = i, p[i]
        elif start is not None:
            peak = max(peak, p[i])
    if start is not None:
        segs.append((t[start], t[-1], peak))
    df = pd.DataFrame(segs, columns=["start_s", "end_s", "score"])
    return df[(df.end_s - df.start_s) >= min_len].reset_index(drop=True)


def temporal_iou(a0, a1, b0, b1):
    inter = max(0.0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union > 0 else 0.0


def match_events(pred, true, iou_thr=0.3):
    """pred, true: DataFrames with fight_id, start_s, end_s (pred also score).

    Returns pred with columns matched (bool), true_idx, iou.
    """
    pred = pred.sort_values("score", ascending=False).copy()
    pred["matched"], pred["true_idx"], pred["iou"] = False, -1, 0.0
    used = set()
    for i, r in pred.iterrows():
        cands = true[true.fight_id == r.fight_id]
        best, best_iou = None, iou_thr
        for j, s in cands.iterrows():
            if j in used:
                continue
            iou = temporal_iou(r.start_s, r.end_s, s.start_s, s.end_s)
            if iou >= best_iou:
                best, best_iou = j, iou
        if best is not None:
            used.add(best)
            pred.loc[i, ["matched", "true_idx", "iou"]] = [True, best, best_iou]
    return pred


def event_metrics(pred, true, total_hours, iou_thr=0.3):
    """Event-level precision/recall/F1, false alarms per fight-hour, start error."""
    m = match_events(pred, true, iou_thr)
    tp = int(m.matched.sum())
    fp = len(m) - tp
    precision = tp / len(m) if len(m) else 0.0
    recall = tp / len(true) if len(true) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if tp else 0.0
    hits = m[m.matched]
    start_err = (hits.start_s.values - true.loc[hits.true_idx, "start_s"].values) if tp else []
    return {
        "n_true": len(true), "n_pred": len(m), "tp": tp, "fp": fp,
        "precision": precision, "recall": recall, "f1": f1,
        "false_alarms_per_hour": fp / total_hours if total_hours else float("nan"),
        "median_abs_start_err_s": float(np.median(np.abs(start_err))) if tp else float("nan"),
    }
