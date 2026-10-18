# Eval harness (Phases 2, 4, 5)

These are the evaluation rules from [docs/PLAN.md](../../docs/PLAN.md), written as code so a model can't break them by accident. It depends only on numpy, pandas and scikit-learn. Revised after [the critique](../../research/critique/CRITIQUE.md), rows #5, #6, #7, #9, #10, #12, #19, #21.

| Module | What it does | Used in |
|---|---|---|
| `splits.py` | `lock_test_groups()`: a fight is in the test set iff `sha1(salt:fight_id) < 0.2`. The salt is frozen in a JSON file, so no fight ever changes side and fights labeled late reach test at the same rate as early ones. `group_cv()` gives GroupKFold or leave-one-group-out splits and fails on any group overlap. `purge_shared_fighters()` drops training rows whose attacker or defender also appears on the evaluation side. | 2, 4, 5 |
| `events.py` | `segments_from_probs()` turns window probabilities into segments (on 0.6 / off 0.4 / min 1.5 s; closes at scene cuts). `event_metrics()`: event F1 at temporal IoU ≥ 0.3, matched within **fight + round**, so round-clock times are safe. It also reports false alarms per hour (only over **exhaustively** labeled hours) and median start error. | 4 |
| `horizons.py` | `normalize_labels()` reads `phase3_labels/labels.csv` ([LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md), the source of truth) or PLAN-style codes, and **raises** on unknown columns or codes instead of returning nothing. **`bell` is censored** (dropped from scoring and counted), not a failure. `horizon_frame()` lists the (attempt, t) rows to predict: duration ≥ t + 2 s. `horizon_metrics()`: ROC-AUC, PR-AUC, Brier score, fight-bootstrap 95% CIs, and `estimable=False` when > 5% of resamples were single-class. `compare_to_baseline()` refuses a baseline that's constant within a horizon (e.g. elapsed time). `LEAKY_COLUMNS` / `assert_no_leaky_features()` block label and future columns such as `seconds_to_lock`. | 5 |

## Run the tests (11 pass, about 20 s on CPU)

This project folder can have a long Windows path, and scikit-learn fails to load its DLL from deep paths (`WinError 206`). Keep the venv at a short path:

```bash
python -m venv C:/Users/netan/.venvs/ufc-eval
```
```bash
C:/Users/netan/.venvs/ufc-eval/Scripts/python.exe -m pip install numpy pandas scikit-learn pytest
```
```bash
C:/Users/netan/.venvs/ufc-eval/Scripts/python.exe -m pytest -q -p no:cacheprovider tools/eval_harness
```

## Typical use (Phase 5)

```python
from horizons import horizon_frame, horizon_metrics, compare_to_baseline, assert_no_leaky_features
hf = horizon_frame(labels)                 # labels.csv rows; bell attempts are censored
assert_no_leaky_features(feature_cols)
hf["p"] = model_predict(hf)                # frames <= attempt start + t only
hf["p_base"] = stats_baseline_predict(hf)  # as-of-date fighter priors + round time
print(horizon_metrics(hf))
print(compare_to_baseline(hf))             # beats_baseline is True only if the CI lower bound > 0
```
