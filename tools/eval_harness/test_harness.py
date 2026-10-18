"""Synthetic checks for the harness. Run: python -m pytest -q tools/eval_harness"""
import numpy as np
import pandas as pd
import pytest

from events import event_metrics, segments_from_probs, temporal_iou
from horizons import (compare_to_baseline, eligible_at, horizon_frame,
                      horizon_metrics, label_attempts, reliability)
from splits import assert_no_group_leak, group_cv, lock_test_groups, train_test_mask


def fake_attempts(n_fights=60, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for f in range(n_fights):
        for k in range(rng.integers(1, 3)):
            start = rng.uniform(10, 200)
            dur = rng.uniform(1.5, 25)
            y = rng.random() < 0.4
            outcome = rng.choice(["SUCCESS_TAP", "SUCCESS_REF"]) if y else \
                rng.choice(["FAIL_ESCAPE", "FAIL_POSITION_CHANGE", "FAIL_BELL"])
            rows.append({"attempt_id": f"F{f}_r1_{k}", "fight_id": f"F{f}",
                         "start_s": start, "end_s": start + dur, "outcome": outcome})
    rows.append({"attempt_id": "F0_r2_9", "fight_id": "F0", "start_s": 1, "end_s": 5,
                 "outcome": "EXCLUDE"})
    return pd.DataFrame(rows)


# ---- splits
def test_lock_is_stable(tmp_path):
    path = tmp_path / "lock.json"
    first = lock_test_groups([f"F{i}" for i in range(50)], path=path)
    again = lock_test_groups([f"F{i}" for i in range(80)], seed=99, path=path)
    assert first == again and len(first) == 10


def test_group_cv_never_leaks():
    groups = np.repeat([f"F{i}" for i in range(12)], 30)
    for tr, va in group_cv(groups, n_splits=4):
        assert not set(groups[tr]) & set(groups[va])
    assert sum(1 for _ in group_cv(groups, n_splits=None)) == 12
    with pytest.raises(AssertionError):
        assert_no_group_leak(["A", "B"], ["B"])
    assert train_test_mask(["A", "B", "A"], ["A"]).tolist() == [True, False, True]


# ---- events
def test_hysteresis_segments_and_cut_reset():
    t = np.arange(0, 20, 0.5)
    p = np.where((t >= 3) & (t < 9), 0.9, 0.1)
    p[(t >= 4) & (t < 5)] = 0.5          # dips above `off`: segment stays open
    segs = segments_from_probs(t, p)
    assert len(segs) == 1 and segs.start_s[0] == 3 and segs.end_s[0] == 8.5
    split = segments_from_probs(t, p, resets=[6.0], min_len=0)
    assert len(split) == 2               # the cut closes it; p is still high so it reopens


def test_event_metrics():
    true = pd.DataFrame({"fight_id": ["A", "A", "B"], "start_s": [10, 50, 5], "end_s": [20, 60, 15]})
    pred = pd.DataFrame({"fight_id": ["A", "A", "B"], "start_s": [11, 100, 30],
                         "end_s": [19, 110, 40], "score": [0.9, 0.8, 0.7]})
    m = event_metrics(pred, true, total_hours=0.5)
    assert m["tp"] == 1 and m["fp"] == 2 and m["false_alarms_per_hour"] == 4
    assert m["recall"] == pytest.approx(1 / 3) and m["median_abs_start_err_s"] == 1
    assert temporal_iou(0, 10, 5, 15) == pytest.approx(5 / 15)


# ---- horizons
def test_eligibility_excludes_near_outcome():
    a = label_attempts(fake_attempts())
    assert "EXCLUDE" not in set(a.outcome)
    for t in (1, 3, 8):
        ok = a[eligible_at(a, t)]
        assert (ok.duration_s >= t + 2).all()
    hf = horizon_frame(fake_attempts())
    assert hf.groupby("t").size().is_monotonic_decreasing


def test_signal_beats_noise_and_baseline():
    rng = np.random.default_rng(1)
    hf = horizon_frame(fake_attempts(n_fights=120))
    hf["p"] = np.clip(0.4 + 0.35 * (hf.y - 0.4) + rng.normal(0, 0.15, len(hf)), 0, 1)
    hf["p_base"] = rng.random(len(hf))
    res = horizon_metrics(hf, n_boot=200)
    assert (res.roc_auc > 0.75).all() and (res.roc_auc_ci_lo < res.roc_auc).all()
    cmp = compare_to_baseline(hf, n_boot=200)
    assert cmp["beats_baseline"]
    rel = reliability(hf.y, hf.p)
    assert rel.n.sum() == len(hf)
