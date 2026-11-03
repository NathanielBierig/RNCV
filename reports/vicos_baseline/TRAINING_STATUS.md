# Phase 2 status (VICOS positions + 2b pose smoke test)

Updated 2026-10-18. All runs use 5 time-block folds (all cameras of a moment together, 300-frame purge) on the laptop CPU.

## Position classifier (18 classes)

| Model | Macro-F1 | Swap macro-F1 | Macro-F1, 10 positions (roles merged) | Balanced acc. |
|---|---|---|---|---|
| GBM | 0.46 | 0.60 | 0.52 | 0.47 |
| **GBM + swap augmentation** | **0.63** | **0.63** | **0.67** | **0.63** |
| MLP | 0.45 | 0.55 | 0.50 | 0.45 |
| MLP + swap augmentation | 0.58 | 0.58 | 0.62 | 0.58 |
| MLP, role-invariant features | 0.59 | 0.59 (exact) | 0.63 | 0.59 |
| MLP, role-invariant + swap aug (no-op check) | 0.58 | 0.58 (exact) | 0.63 | 0.58 |
| GBM, role-invariant features | 0.62 | 0.62 (exact) | 0.66 | 0.62 |
| Always guess majority class | - | - | - | 0.14 (accuracy) |

**Role-invariant features (`--features rolinv`, `src/features.py: build_role_invariant`).** The two athletes are put in a canonical order (the athlete whose hips are higher in the image goes first, the "top" athlete), and pair features are symmetrized (distance matrix `(D+Dᵀ)/2` and `|D−Dᵀ|`, per-athlete min/max, |hip height gap|), 350 features in all. The vector is **identical under a pose1↔pose2 swap** (verified on all 120,279 frames). A symmetric vector can't tell `mount1` from `mount2` by itself, because those labels name a specific athlete. So the model learns **canonical labels** ("suffix athlete is top / bottom"), and predictions are mapped back. That makes the 18-class output exactly swap-equivariant (swap macro-F1 = macro-F1 to every digit), with no augmentation needed. Swap augmentation becomes a no-op: the rolinv+swap-aug run differs only by MLP training noise.

**Verdict:** role-invariant features match swap augmentation within about 0.01 (GBM 0.62 vs 0.63; MLP 0.59 vs 0.58; back recall 0.77 vs 0.78). Per class they're within 0.03 everywhere except 50-50 guard (0.70 vs 0.76). Swap augmentation already got the model to near-equivariance (swap gap 0.002), so the exact guarantee doesn't buy accuracy on VICOS. **Default stays GBM + swap augmentation** (best score, 178 features, ~2–3× faster per fold than rolinv's 350). Keep `--features rolinv` for UFC, where its canonical top/bottom order gives the RNC stage a ready-made attacker/defender split. Run times: GBM rolinv folds took ~15 min each with the CPU shared with a pose run.

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

## Reproduce (from )

```powershell
python -I src/train_baseline.py --model gbm --swap-aug --tag _swapaug
python -I src/back_rule.py
python -I src/pose_smoke.py
```
