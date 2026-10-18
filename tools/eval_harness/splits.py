"""Leak-proof splits: everything is grouped by fight (or VICOS segment).

lock_test_groups() picks the held-out fights once and writes them to JSON.
Calling it again with the same path returns the saved lock, even if new
fights were added, so the test set can never drift.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut


def lock_test_groups(groups, frac=0.2, seed=0, path=None):
    """Return a sorted list of held-out group ids. Persist to `path` if given."""
    if path is not None and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)["test_groups"]
    uniq = np.array(sorted(set(map(str, groups))))
    n_test = max(1, int(round(frac * len(uniq))))
    rng = np.random.default_rng(seed)
    test = sorted(rng.choice(uniq, size=n_test, replace=False).tolist())
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"seed": seed, "frac": frac, "n_groups_at_lock": len(uniq),
                       "test_groups": test}, f, indent=2)
    return test


def train_test_mask(groups, test_groups):
    """Boolean mask: True = row belongs to the locked test set."""
    test = set(map(str, test_groups))
    return np.array([str(g) in test for g in groups])


def group_cv(groups, n_splits=5):
    """Yield (train_idx, val_idx). n_splits=None -> leave-one-group-out."""
    groups = np.asarray(groups)
    cv = LeaveOneGroupOut() if n_splits is None else GroupKFold(n_splits=n_splits)
    for tr, va in cv.split(np.zeros(len(groups)), groups=groups):
        assert_no_group_leak(groups[tr], groups[va])
        yield tr, va


def assert_no_group_leak(train_groups, test_groups):
    overlap = set(map(str, train_groups)) & set(map(str, test_groups))
    if overlap:
        raise AssertionError(f"groups on both sides of the split: {sorted(overlap)[:5]}")
