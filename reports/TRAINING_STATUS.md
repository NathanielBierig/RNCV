# Phase 2 status (VICOS positions + 2b pose smoke test)

Updated 2026-10-18. All runs use 5 time-block folds (all cameras of a moment together, 300-frame purge) on the laptop CPU.

## Position classifier (18 classes)

| Model | Macro-F1 | Swap macro-F1 | Macro-F1, 10 positions (roles merged) | Balanced acc. |
|---|---|---|---|---|
| GBM | 0.46 | 0.60 | 0.52 | 0.47 |
| **GBM + swap augmentation** | **0.63** | **0.63** | **0.67** | **0.63** |
| MLP | 0.45 | 0.55 | 0.50 | 0.45 |
| MLP + swap augmentation | 0.58 | 0.58 | 0.62 | 0.58 |
| Always guess majority class | - | - | - | 0.14 (accuracy) |

- **Swap augmentation (critique #13) is the single biggest win:** +0.17 macro-F1, and the model becomes athlete-order invariant (swap macro-F1 equals normal macro-F1). That's required for UFC, where tracker IDs are arbitrary.
- **Per-fold F1 is now computed honestly (critique #18):** false positives into classes absent from a test block count. The old per-fold range (0.45–0.66) was inflated; the honest range for plain GBM is 0.22–0.48 (swap-aug: 0.32–0.50). Pooled numbers were already correct and are unchanged.
- **Still weak:** half guard (0.27/0.33), takedowns (0.38/0.48), side control/mount (0.48–0.55). Strong: standing 0.93, turtle 0.83–0.87, open guard 0.77–0.83, closed_guard1 0.80, back 0.77–0.79.
- GBM beats the MLP in both settings, so GBM + swap aug is the default model.

## Back control: classifier vs geometry rule (critique #1c), `reports/back_rule.md`

| Method | Back recall | Recall, both athletes visible | Precision | F1 |
|---|---|---|---|---|
| Geometry rule (thresholds tuned on train blocks) | 0.41 | 0.83 | 0.59 | 0.48 |
| GBM + swap aug | **0.78** | **0.92** | **0.85** | **0.81** |

- Only **49%** of VICOS back frames have poses for *both* athletes, which caps any two-skeleton rule at ~0.49 recall. Where both are visible, the rule finds 83% of back frames and picks the right attacker in 84% of its hits, with no training on these athletes.
- The classifier wins on VICOS, but every back frame comes from one session of one athlete pair. **The deciding test is hand-tagged UFC frames** (critique #1a). Keep both until then.

## Pose smoke test (Phase 2b), `reports/pose_smoke.md`

- `src/pose_smoke.py` runs end to end: RTMO-m via rtmlib + onnxruntime at **~2.8–2.9 fps on this laptop CPU** (a 60 s clip at stride 3 takes about 4 min).
- It was tested on `tools/overlay/demo_clip.mp4`, which is **synthetic (no people)**, so 0% coverage is the expected result there. The real coverage numbers need the user's UFC clips in `data/clips/`.

## Notes

- Two folds took 1–1.7 h instead of ~5 min, probably because the laptop slept mid-run. Use `--train-stride 4` for faster runs.
- `src/vicos_data.py`: the dead `lo = {},` line flagged in critique #18 is removed.

## Reproduce (from C:\Users\netan\projects\RNCV)

```powershell
C:\Users\netan\.venvs\rncv\Scripts\python -I src/train_baseline.py --model gbm --swap-aug --tag _swapaug
C:\Users\netan\.venvs\rncv\Scripts\python -I src/back_rule.py
C:\Users\netan\.venvs\rncv\Scripts\python -I src/pose_smoke.py
```
