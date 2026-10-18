"""Phase 4: turn window probabilities into attempt segments and score them.

A predicted segment is a hit if its temporal IoU with an unmatched true
attempt in the same fight (and round, when both tables have one) is >= iou_thr
(greedy, highest score first). Times are whatever clock both tables share;
with the round clock of LABEL_SCHEMA the `round` column is required.
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


def _keys(pred, true):
    keys = ["fight_id"]
    if "round" in pred.columns and "round" in true.columns:
        keys.append("round")
    elif "round" in pred.columns or "round" in true.columns:
        raise ValueError("`round` is in only one table; round-clock times need it in both")
    return keys


def match_events(pred, true, iou_thr=0.3):
    """pred, true: DataFrames with fight_id, start_s, end_s (pred also score).

    Returns pred (fresh 0..n-1 index) with columns matched (bool), true_pos
    (row position in `true`, -1 if unmatched) and iou.
    """
    keys = _keys(pred, true)
    true = true.reset_index(drop=True)
    pred = pred.sort_values("score", ascending=False).reset_index(drop=True)
    pred["matched"], pred["true_pos"], pred["iou"] = False, -1, 0.0
    by_key = {k: g for k, g in true.groupby(keys)}
    used = set()
    for i, r in pred.iterrows():
        cands = by_key.get(tuple(r[c] for c in keys))
        if cands is None:
            continue
        best, best_iou = None, iou_thr
        for j, s in cands.iterrows():
            if j in used:
                continue
            iou = temporal_iou(r.start_s, r.end_s, s.start_s, s.end_s)
            if iou >= best_iou:
                best, best_iou = j, iou
        if best is not None:
            used.add(best)
            pred.loc[i, ["matched", "true_pos", "iou"]] = [True, best, best_iou]
    return pred


def event_metrics(pred, true, total_hours, iou_thr=0.3):
    """Event-level precision/recall/F1, false alarms per hour, start error.

    `total_hours` must be footage that was *exhaustively* labeled; hours where
    only candidate segments were reviewed would make false alarms look rarer.
    """
    true = true.reset_index(drop=True)
    m = match_events(pred, true, iou_thr)
    tp = int(m.matched.sum())
    fp = len(m) - tp
    precision = tp / len(m) if len(m) else 0.0
    recall = tp / len(true) if len(true) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if tp else 0.0
    hits = m[m.matched]
    start_err = hits.start_s.values - true.start_s.values[hits.true_pos.astype(int)]
    return {
        "n_true": len(true), "n_pred": len(m), "tp": tp, "fp": fp,
        "precision": precision, "recall": recall, "f1": f1,
        "false_alarms_per_hour": fp / total_hours if total_hours else float("nan"),
        "median_abs_start_err_s": float(np.median(np.abs(start_err))) if tp else float("nan"),
    }
