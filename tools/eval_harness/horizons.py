"""Phase 5: leak-free evaluation of finish probability at fixed horizons.

At horizon t (seconds after attempt start) an attempt is eligible only if it
is still ongoing and its outcome is at least `min_gap` seconds away, i.e.
duration >= t + min_gap. Predictions must use frames <= start + t only;
that part is the model's job, this module enforces who gets scored.

`bell` is censoring, not failure: the choke was still on when time ran out.
By default bell attempts are dropped from scoring (counted as n_censored).

All confidence intervals bootstrap over fights, not rows.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

SUCCESS = {"tap", "ref_stop", "unconscious"}
FAILURE = {"escape", "position_change"}
CENSORED = {"bell"}
HORIZONS = (1, 2, 3, 5, 8)

# Columns that describe the whole attempt or its future. Never model inputs.
LEAKY_COLUMNS = {
    "outcome", "success", "y", "attempt_end_s", "end_s", "duration_s",
    "seconds_to_lock", "choke_arm_depth", "deepest_point", "labeler_conf",
    "confidence", "notes", "video_time_end",
}

# PLAN.md §3.4 codes -> LABEL_SCHEMA.md codes (LABEL_SCHEMA is the source of truth)
_PLAN_CODES = {
    "SUCCESS_TAP": "tap", "SUCCESS_REF": "ref_stop", "SUCCESS_UNCONSCIOUS": "unconscious",
    "FAIL_ESCAPE": "escape", "FAIL_POSITION_CHANGE": "position_change", "FAIL_BELL": "bell",
}


def normalize_labels(labels, clean_only=False):
    """Accept phase3_labels/labels.csv (LABEL_SCHEMA.md) or PLAN §3.4 rows.

    Returns a frame with attempt_id, fight_id, round (if given), start_s,
    end_s, outcome (LABEL_SCHEMA codes). Fails loudly instead of silently
    returning zero rows.
    """
    a = labels.rename(columns={"attempt_start_s": "start_s", "attempt_end_s": "end_s"}).copy()
    missing = {"fight_id", "start_s", "end_s", "outcome"} - set(a.columns)
    if missing:
        raise ValueError(f"label table is missing columns: {sorted(missing)}")
    a["outcome"] = a.outcome.astype(str).str.strip().replace(_PLAN_CODES)
    a = a[a.outcome != "EXCLUDE"]
    if "sub_type" in a.columns:
        a = a[a.sub_type.fillna("rnc") == "rnc"]
    if clean_only and "camera_cut_flag" in a.columns:
        a = a[a.camera_cut_flag != "cut_out"]
    unknown = set(a.outcome) - SUCCESS - FAILURE - CENSORED
    if unknown:
        raise ValueError(f"unknown outcome codes: {sorted(unknown)}")
    if (a.end_s <= a.start_s).any():
        raise ValueError("rows with end <= start")
    if "attempt_id" not in a.columns:
        rnd = a["round"].astype(str) if "round" in a.columns else "0"
        a["attempt_id"] = a.fight_id.astype(str) + "_r" + rnd + "_" + \
            a.groupby(["fight_id"] + (["round"] if "round" in a.columns else [])).cumcount().astype(str)
    if a.empty:
        raise ValueError("no usable RNC rows after normalization")
    return a.reset_index(drop=True)


def label_attempts(labels, censored="drop"):
    """Normalize, add y (1 = finish) and duration_s. censored: 'drop' or 'fail'."""
    a = normalize_labels(labels)
    if censored == "drop":
        a = a[~a.outcome.isin(CENSORED)].copy()
    a["y"] = a.outcome.isin(SUCCESS).astype(int)
    a["duration_s"] = a.end_s - a.start_s
    return a


def eligible_at(attempts, t, min_gap=2.0):
    """Boolean mask of attempts that may be scored at horizon t."""
    return (attempts.end_s - attempts.start_s) >= t + min_gap


def horizon_frame(labels, horizons=HORIZONS, min_gap=2.0, censored="drop"):
    """Long table (attempt_id, fight_id, t, y): the rows a model must predict.

    Attributes: .attrs['n_censored'] = bell attempts left out per horizon.
    """
    all_a = normalize_labels(labels)
    a = label_attempts(labels, censored)
    cols = ["attempt_id", "fight_id", "y"] + [c for c in ("round", "start_s") if c in a.columns]
    rows = [a.loc[eligible_at(a, t, min_gap), cols].assign(t=t) for t in horizons]
    out = pd.concat(rows, ignore_index=True)
    cens = all_a[all_a.outcome.isin(CENSORED)]
    out.attrs["n_censored"] = {t: int(eligible_at(cens, t, min_gap).sum()) for t in horizons}
    return out


def assert_no_leaky_features(feature_columns):
    leaked = set(feature_columns) & LEAKY_COLUMNS
    if leaked:
        raise AssertionError(f"future/label columns used as features: {sorted(leaked)}")


def _metrics(y, p):
    if len(np.unique(y)) < 2:
        return {"roc_auc": np.nan, "pr_auc": np.nan, "brier": brier_score_loss(y, p)}
    return {"roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
            "brier": brier_score_loss(y, p)}


def _fight_bootstrap(df, fn, n_boot, seed):
    """Returns (ci_lo, ci_hi, frac_dropped). Single-class resamples are dropped."""
    rng = np.random.default_rng(seed)
    by_fight = {f: g for f, g in df.groupby("fight_id")}
    fights = np.array(list(by_fight))
    out = []
    for _ in range(n_boot):
        val = fn(pd.concat([by_fight[f] for f in rng.choice(fights, len(fights))]))
        if not np.isnan(val):
            out.append(val)
    dropped = 1 - len(out) / n_boot
    lo, hi = np.percentile(out, [2.5, 97.5]) if out else (np.nan, np.nan)
    return lo, hi, dropped


def horizon_metrics(preds, n_boot=1000, seed=0, max_dropped=0.05):
    """preds: DataFrame with fight_id, t, y, p. Returns one row per horizon.

    `estimable` is False when more than `max_dropped` of bootstrap resamples
    had a single class, i.e. the CI would be overconfident.
    """
    rows = []
    for t, g in preds.groupby("t"):
        m = _metrics(g.y.values, g.p.values)
        lo, hi, dropped = _fight_bootstrap(
            g, lambda s: _metrics(s.y.values, s.p.values)["roc_auc"], n_boot, seed)
        rows.append({"t": t, "n": len(g), "n_pos": int(g.y.sum()),
                     "n_fights": g.fight_id.nunique(), **m,
                     "roc_auc_ci_lo": lo, "roc_auc_ci_hi": hi,
                     "boot_dropped": dropped, "estimable": dropped <= max_dropped})
    return pd.DataFrame(rows)


def check_baseline_not_degenerate(preds, p_base="p_base"):
    """A baseline constant within every horizon has AUC 0.5 by construction."""
    if preds.groupby("t")[p_base].nunique().max() <= 1:
        raise ValueError(f"{p_base} is constant within each horizon (e.g. elapsed time); "
                         "it cannot rank attempts, so beating it means nothing")


def compare_to_baseline(preds, p_model="p", p_base="p_base", n_boot=1000, seed=0):
    """Paired fight bootstrap of mean ROC-AUC difference (model - baseline) across horizons."""
    check_baseline_not_degenerate(preds, p_base)

    def mean_diff(s):
        d = [_metrics(g.y.values, g[p_model].values)["roc_auc"]
             - _metrics(g.y.values, g[p_base].values)["roc_auc"] for _, g in s.groupby("t")]
        return np.nanmean(d) if d else np.nan
    point = mean_diff(preds)
    lo, hi, dropped = _fight_bootstrap(preds, mean_diff, n_boot, seed)
    return {"mean_auc_diff": point, "ci_lo": lo, "ci_hi": hi,
            "boot_dropped": dropped, "beats_baseline": bool(lo > 0)}


def reliability(y, p, n_bins=10):
    """Calibration table: mean predicted vs observed finish rate per bin."""
    df = pd.DataFrame({"y": y, "p": p})
    df["bin"] = np.minimum((df.p * n_bins).astype(int), n_bins - 1)
    return df.groupby("bin").agg(n=("y", "size"), mean_p=("p", "mean"),
                                 frac_finish=("y", "mean")).reset_index()
