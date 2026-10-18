"""Synthetic checks for the harness. Run: python -m pytest -q tools/eval_harness"""
import numpy as np
import pandas as pd
import pytest

from events import event_metrics, segments_from_probs, temporal_iou
from horizons import (assert_no_leaky_features, compare_to_baseline, eligible_at,
                      horizon_frame, horizon_metrics, label_attempts,
                      normalize_labels, reliability)
from splits import (assert_no_group_leak, group_cv, lock_test_groups,
                    purge_shared_fighters, train_test_mask)


def fake_labels(n_fights=60, seed=0):
    """Rows in phase3_labels/LABEL_SCHEMA.md format."""
    rng = np.random.default_rng(seed)
    rows = []
    for f in range(n_fights):
        for k in range(rng.integers(1, 3)):
            start = rng.uniform(10, 200)
            dur = rng.uniform(1.5, 25)
            y = rng.random() < 0.4
            outcome = rng.choice(["tap", "ref_stop"]) if y else \
                rng.choice(["escape", "position_change", "bell"])
            rows.append({"fight_id": f"F{f}", "round": 1 + k, "attempt_start_s": start,
                         "attempt_end_s": start + dur, "outcome": outcome, "sub_type": "rnc",
                         "attacker": f"A{f % 40}", "defender": f"D{f}"})
    rows.append({"fight_id": "F0", "round": 3, "attempt_start_s": 1, "attempt_end_s": 5,
                 "outcome": "escape", "sub_type": "not_a_choke", "attacker": "x", "defender": "y"})
    return pd.DataFrame(rows)


# ---- splits
def test_lock_rule_is_frozen_and_grows(tmp_path):
    path = tmp_path / "lock.json"
    early = lock_test_groups([f"F{i}" for i in range(50)], path=path)
    later = lock_test_groups([f"F{i}" for i in range(500)], salt="other", path=path)
    assert set(early) <= set(later)                      # no fight changes side
    assert any(int(g[1:]) >= 50 for g in later)          # late fights also reach test
    assert 0.12 < len(later) / 500 < 0.28


def test_group_cv_never_leaks():
    groups = np.repeat([f"F{i}" for i in range(12)], 30)
    for tr, va in group_cv(groups, n_splits=4):
        assert not set(groups[tr]) & set(groups[va])
    assert sum(1 for _ in group_cv(groups, n_splits=None)) == 12
    with pytest.raises(AssertionError):
        assert_no_group_leak(["A", "B"], ["B"])
    assert train_test_mask(["A", "B", "A"], ["A"]).tolist() == [True, False, True]


def test_purge_shared_fighters():
    att = np.array(["A", "B", "C", "A"])
    dfd = np.array(["X", "Y", "Z", "W"])
    kept = purge_shared_fighters(np.array([1, 2, 3]), np.array([0]), att, dfd)
    assert kept.tolist() == [1, 2]                       # row 3 shares attacker A


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


def test_events_respect_round_and_duplicate_index():
    true = pd.concat([pd.DataFrame({"fight_id": ["A"], "round": [2], "start_s": [120], "end_s": [130]}),
                      pd.DataFrame({"fight_id": ["B"], "round": [1], "start_s": [50], "end_s": [60]})])
    assert list(true.index) == [0, 0]                    # duplicate index from concat
    pred = pd.DataFrame({"fight_id": ["A", "B"], "round": [1, 1], "start_s": [120, 50],
                         "end_s": [130, 60], "score": [0.9, 0.8]})
    m = event_metrics(pred, true, total_hours=1)
    assert m["tp"] == 1 and m["fp"] == 1                 # round-1 pred must not match round-2 truth
    with pytest.raises(ValueError):
        event_metrics(pred.drop(columns="round"), true, total_hours=1)


# ---- horizons
def test_schema_is_read_and_fails_loudly():
    a = normalize_labels(fake_labels())
    assert {"start_s", "end_s", "attempt_id"} <= set(a.columns)
    assert "not_a_choke" not in set(a.get("sub_type", []))
    with pytest.raises(ValueError):
        normalize_labels(fake_labels().assign(outcome="TAPPED"))
    with pytest.raises(ValueError):
        normalize_labels(fake_labels().drop(columns="attempt_end_s"))
    plan_style = pd.DataFrame({"attempt_id": ["x"], "fight_id": ["F"], "start_s": [0.0],
                               "end_s": [9.0], "outcome": ["SUCCESS_TAP"]})
    assert normalize_labels(plan_style).outcome[0] == "tap"


def test_bell_is_censored_and_eligibility():
    labels = fake_labels()
    a = label_attempts(labels)
    assert "bell" not in set(a.outcome)
    assert len(label_attempts(labels, censored="fail")) > len(a)
    for t in (1, 3, 8):
        assert (a[eligible_at(a, t)].duration_s >= t + 2).all()
    hf = horizon_frame(labels)
    assert hf.groupby("t").size().is_monotonic_decreasing
    assert sum(hf.attrs["n_censored"].values()) > 0


def test_signal_beats_noise_and_baseline():
    rng = np.random.default_rng(1)
    hf = horizon_frame(fake_labels(n_fights=120))
    hf["p"] = np.clip(0.4 + 0.35 * (hf.y - 0.4) + rng.normal(0, 0.15, len(hf)), 0, 1)
    hf["p_base"] = rng.random(len(hf))
    res = horizon_metrics(hf, n_boot=200)
    assert (res.roc_auc > 0.75).all() and (res.roc_auc_ci_lo < res.roc_auc).all()
    assert res.estimable.all()
    cmp = compare_to_baseline(hf, n_boot=200)
    assert cmp["beats_baseline"]
    rel = reliability(hf.y, hf.p)
    assert rel.n.sum() == len(hf)


def test_degenerate_baseline_and_leaky_features_rejected():
    hf = horizon_frame(fake_labels())
    hf["p"], hf["p_base"] = 0.5, hf.t / 10               # elapsed time only
    with pytest.raises(ValueError):
        compare_to_baseline(hf, n_boot=10)
    with pytest.raises(AssertionError):
        assert_no_leaky_features(["arm_under_chin", "seconds_to_lock"])
    assert_no_leaky_features(["arm_under_chin", "t"])


def test_tiny_horizon_marked_not_estimable():
    df = pd.DataFrame({"fight_id": ["a", "b", "c", "d"], "t": 8, "y": [1, 0, 0, 0],
                       "p": [0.9, 0.1, 0.2, 0.3]})
    assert not horizon_metrics(df, n_boot=200).estimable[0]
