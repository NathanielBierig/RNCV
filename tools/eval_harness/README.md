# Eval harness (Phases 2, 4, 5)

These are the evaluation rules from [docs/PLAN.md](../../docs/PLAN.md), written as code so a model can't break them by accident. It depends only on numpy, pandas and scikit-learn.

| Module | What it does | Used in |
|---|---|---|
| `splits.py` | `lock_test_groups()` picks the held-out fights **once** and saves them to JSON; later calls return the same set. `group_cv()` gives GroupKFold or leave-one-group-out splits and fails if a fight/segment ends up on both sides. | 2 (VICOS segments), 4, 5 |
| `events.py` | `segments_from_probs()` turns per-window probabilities into attempt segments (on 0.6 / off 0.4 / min 1.5 s; closes at scene cuts). `event_metrics()` scores them: event F1 at temporal IoU ≥ 0.3, false alarms per fight-hour, median start error. | 4 |
| `horizons.py` | `horizon_frame()` lists the (attempt, t) rows a model must predict. An attempt only counts at horizon t if it lasts ≥ t + 2 s, so its outcome is still at least 2 s away. `horizon_metrics()` reports ROC-AUC, PR-AUC, Brier score and 95% CIs bootstrapped **by fight**. `compare_to_baseline()` runs a paired bootstrap against the stats-only baseline. `reliability()` gives the calibration table. | 5 |

Input schema: `phase3_labels` rows with `attempt_id, fight_id, start_s, end_s, outcome` (outcome codes are in PLAN.md §3.4; `EXCLUDE` rows get dropped).

## Run the tests (6 pass, about 30 s on CPU)

This project folder has a very long Windows path, and scikit-learn fails to load its DLL from deep in it (`WinError 206`). Keep the venv at a short path:

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
from horizons import horizon_frame, horizon_metrics, compare_to_baseline
hf = horizon_frame(attempts)              # rows the model must score
hf["p"] = model_predict(hf)               # your model: frames <= start_s + t only
hf["p_base"] = stats_baseline_predict(hf) # fighter priors + round time
print(horizon_metrics(hf))
print(compare_to_baseline(hf))            # beats_baseline is True only if the CI lower bound > 0
```
