# No-pose RNC attempt detector (CLIP ViT-B-32 + logistic regression)

Frames sampled at 2.0/s from every labeled clip (+ watched no-RNC rounds). Positive = inside a labeled attempt window. **Leave-one-fight-out:** each fight is scored by a model that never saw it.

| Held-out fight | Frames | % inside attempts | ROC-AUC | PR-AUC (base rate) |
|---|---|---|---|---|
| 4dc5039b | 490 | 26% | 0.86 | 0.58 (0.26) |
| 4f9939af | 183 | 15% | 0.58 | 0.22 (0.15) |
| 652a956a | 52 | 15% | 0.20 | 0.10 (0.15) |
| 6c44af21 | 43 | 14% | 0.76 | 0.33 (0.14) |
| 755202fc | 32 | 16% | 0.25 | 0.12 (0.16) |
| 79865287 | 107 | 35% | 0.70 | 0.65 (0.35) |
| 7d4c160d | 117 | 15% | 0.79 | 0.57 (0.15) |
| 7d4e49d8 | 83 | 24% | 0.53 | 0.27 (0.24) |
| 800a35b3 | 604 | 15% | 0.63 | 0.19 (0.15) |
| 83084647 | 139 | 28% | 0.69 | 0.48 (0.28) |
| 919fb76d | 28 | 18% | 0.74 | 0.33 (0.18) |
| b22eab3a | 67 | 57% | 0.38 | 0.48 (0.57) |
| c03b6b6c | 128 | 60% | 0.70 | 0.81 (0.60) |
| d85c76a6 | 64 | 53% | 0.33 | 0.43 (0.53) |
| e761c500 | 82 | 46% | 0.33 | 0.37 (0.46) |
| e9700d51 | 15 | 33% | 0.98 | 0.97 (0.33) |
| f030febe | 398 | 50% | 0.57 | 0.58 (0.50) |
| f8fce67a | 50 | 34% | 0.95 | 0.86 (0.34) |
| fd49f89b | 97 | 22% | 0.66 | 0.30 (0.22) |

**Pooled (all held-out frames):** ROC-AUC **0.66**, PR-AUC **0.43** (base rate 0.29). With ~2 s smoothing: ROC-AUC 0.68, PR-AUC 0.45.

ROC-AUC 0.5 = guessing, 1.0 = perfect. PR-AUC is compared to the base rate (a guesser scores the base rate).
Caveat: few fights, and some clips are almost all attempt (few negatives), so per-fight AUCs are noisy or undefined (nan).
