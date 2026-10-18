"""Phase 5: leak-free evaluation of finish probability at fixed horizons.

At horizon t (seconds after attempt start) an attempt is eligible only if it
is still ongoing and its outcome is at least `min_gap` seconds away, i.e.
duration >= t + min_gap. Predictions must use frames <= start_s + t only;
that part is the model's job, this module enforces who gets scored.

All confidence intervals bootstrap over fights, not rows.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

SUCCESS = {"SUCCESS_TAP", "SUCCESS_REF", "SUCCESS_UNCONSCIOUS"}
FAILURE = {"FAIL_ESCAPE", "FAIL_POSITION_CHANGE", "FAIL_BELL"}
HORIZONS = (1, 2, 3, 5, 8)


def label_attempts(attempts):
    """Drop EXCLUDE rows, add y (1 = finish) and duration_s."""
    a = attempts[attempts.outcome.isin(SUCCESS | FAILURE)].copy()
    a["y"] = a.outcome.isin(SUCCESS).astype(int)
    a["duration_s"] = a.end_s - a.start_s
    return a


def eligible_at(attempts, t, min_gap=2.0):
    """Boolean mask of attempts that may be scored at horizon t."""
    return (attempts.end_s - attempts.start_s) >= t + min_gap


def horizon_frame(attempts, horizons=HORIZONS, min_gap=2.0):
    """Long table (attempt_id, fight_id, t, y): the rows a model must predict."""
    a = label_attempts(attempts)
    rows = [a.loc[eligible_at(a, t, min_gap), ["attempt_id", "fight_id", "y"]].assign(t=t)
            for t in horizons]
    return pd.concat(rows, ignore_index=True)


def _metrics(y, p):
    if len(np.unique(y)) < 2:
        return {"roc_auc": np.nan, "pr_auc": np.nan, "brier": brier_score_loss(y, p)}
    return {"roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
            "brier": brier_score_loss(y, p)}


def _fight_bootstrap(df, fn, n_boot, seed):
    rng = np.random.default_rng(seed)
    by_fight = {f: g for f, g in df.groupby("fight_id")}
    fights = np.array(list(by_fight))
    out = []
    for _ in range(n_boot):
        sample = pd.concat([by_fight[f] for f in rng.choice(fights, len(fights))])
        val = fn(sample)
        if not np.isnan(val):
            out.append(val)
    return np.percentile(out, [2.5, 97.5]) if out else (np.nan, np.nan)


def horizon_metrics(preds, n_boot=1000, seed=0):
    """preds: DataFrame with fight_id, t, y, p. Returns one row per horizon."""
    rows = []
    for t, g in preds.groupby("t"):
        m = _metrics(g.y.values, g.p.values)
        lo, hi = _fight_bootstrap(
            g, lambda s: _metrics(s.y.values, s.p.values)["roc_auc"], n_boot, seed)
        rows.append({"t": t, "n": len(g), "n_pos": int(g.y.sum()),
                     "n_fights": g.fight_id.nunique(), **m,
                     "roc_auc_ci_lo": lo, "roc_auc_ci_hi": hi})
    return pd.DataFrame(rows)


def compare_to_baseline(preds, p_model="p", p_base="p_base", n_boot=1000, seed=0):
    """Paired fight bootstrap of mean ROC-AUC difference (model - baseline) across horizons."""
    def mean_diff(s):
        d = [_metrics(g.y.values, g[p_model].values)["roc_auc"]
             - _metrics(g.y.values, g[p_base].values)["roc_auc"] for _, g in s.groupby("t")]
        return np.nanmean(d) if d else np.nan
    point = mean_diff(preds)
    lo, hi = _fight_bootstrap(preds, mean_diff, n_boot, seed)
    return {"mean_auc_diff": point, "ci_lo": lo, "ci_hi": hi, "beats_baseline": bool(lo > 0)}


def reliability(y, p, n_bins=10):
    """Calibration table: mean predicted vs observed finish rate per bin."""
    df = pd.DataFrame({"y": y, "p": p})
    df["bin"] = np.minimum((df.p * n_bins).astype(int), n_bins - 1)
    return df.groupby("bin").agg(n=("y", "size"), mean_p=("p", "mean"),
                                 frac_finish=("y", "mean")).reset_index()
