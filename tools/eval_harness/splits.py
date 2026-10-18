"""Leak-proof splits: everything is grouped by fight (or VICOS segment).

Test membership is decided by a salted hash of the fight id, so it is stable
(a fight never changes side) and still grows with the dataset: fights labeled
in week 7 land in test at the same rate as week-4 pilot fights.

Fights are not the only leak: the same fighter recurs across fights.
purge_shared_fighters() drops training rows whose fighters appear in the
evaluation side.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut


def _in_test(group, salt, frac):
    h = hashlib.sha1(f"{salt}:{group}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF < frac


def lock_test_groups(groups, frac=0.2, salt=None, path=None):
    """Return the sorted held-out group ids among `groups`.

    The salt (and frac) are written to `path` on first call and reused after,
    so the rule is frozen while the set of fights keeps growing.
    """
    if path is not None and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        salt, frac = cfg["salt"], cfg["frac"]
    else:
        salt = salt if salt is not None else "rncv-test-v1"
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"salt": salt, "frac": frac,
                           "rule": "sha1(salt:fight_id) < frac"}, f, indent=2)
    return sorted(g for g in set(map(str, groups)) if _in_test(g, salt, frac))


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


def purge_shared_fighters(train_idx, eval_idx, fighters_a, fighters_b):
    """Drop train rows whose attacker or defender also appears in the eval rows."""
    a, b = np.asarray(fighters_a), np.asarray(fighters_b)
    seen = set(a[eval_idx]) | set(b[eval_idx])
    keep = [i for i in train_idx if a[i] not in seen and b[i] not in seen]
    return np.asarray(keep, dtype=int)


def assert_no_group_leak(train_groups, test_groups):
    overlap = set(map(str, train_groups)) & set(map(str, test_groups))
    if overlap:
        raise AssertionError(f"groups on both sides of the split: {sorted(overlap)[:5]}")
