# No-pose RNC attempt detector (CLIP ViT-B-32 + logistic regression), fighter crop

Frames sampled at 2.0/s from every labeled clip (+ watched no-RNC rounds). Positive = inside a labeled attempt window. **Leave-one-fight-out:** each fight is scored by a model that never saw it.

| Held-out fight | Frames | % inside attempts | ROC-AUC | PR-AUC (base rate) |
|---|---|---|---|---|
| 800a35b3 | 604 | 15% | 0.59 | 0.17 (0.15) |
| c03b6b6c | 128 | 60% | 0.70 | 0.79 (0.60) |
| d85c76a6 | 64 | 53% | 0.36 | 0.44 (0.53) |
| e761c500 | 82 | 46% | 0.30 | 0.35 (0.46) |
| f030febe | 398 | 50% | 0.54 | 0.51 (0.50) |
| f8fce67a | 50 | 34% | 0.85 | 0.66 (0.34) |

**Pooled (all held-out frames):** ROC-AUC **0.50**, PR-AUC **0.41** (base rate 0.34). With ~2 s smoothing: ROC-AUC 0.51, PR-AUC 0.43.

ROC-AUC 0.5 = guessing, 1.0 = perfect. PR-AUC is compared to the base rate (a guesser scores the base rate).
Caveat: few fights, and some clips are almost all attempt (few negatives), so per-fight AUCs are noisy or undefined (nan).
