# No-pose RNC attempt detector (CLIP ViT-B-32 + logistic regression), fighter crop

Frames sampled at 2.0/s from every labeled clip (+ watched no-RNC rounds). Positive = inside a labeled attempt window. **Leave-one-fight-out:** each fight is scored by a model that never saw it.

| Held-out fight | Frames | % inside attempts | ROC-AUC | PR-AUC (base rate) |
|---|---|---|---|---|
| 01a4827b | 52 | 15% | 0.26 | 0.13 (0.15) |
| 034c04e4 | 330 | 5% | 0.95 | 0.35 (0.05) |
| 0f51869f | 399 | 19% | 0.93 | 0.66 (0.19) |
| 1535fb65 | 1537 | 3% | 0.60 | 0.04 (0.03) |
| 20d74ed2 | 323 | 7% | 0.98 | 0.74 (0.07) |
| 241a0833 | 351 | 9% | 0.88 | 0.35 (0.09) |
| 2ba11e0b | 374 | 14% | 0.90 | 0.56 (0.14) |
| 301f230c | 372 | 9% | 0.73 | 0.31 (0.09) |
| 3ab0d8b3 | 333 | 7% | 0.26 | 0.05 (0.07) |
| 3eea92e7 | 318 | 6% | 0.65 | 0.08 (0.06) |
| 4dc5039b | 490 | 26% | 0.89 | 0.65 (0.26) |
| 4f9939af | 183 | 15% | 0.66 | 0.23 (0.15) |
| 68fe62ba | 304 | 1% | 0.66 | 0.02 (0.01) |
| 6c44af21 | 43 | 14% | 0.66 | 0.21 (0.14) |
| 755202fc | 32 | 16% | 0.13 | 0.11 (0.16) |
| 79865287 | 107 | 45% | 0.72 | 0.69 (0.45) |
| 7d4c160d | 117 | 15% | 0.78 | 0.58 (0.15) |
| 7d4e49d8 | 83 | 24% | 0.62 | 0.35 (0.24) |
| 800a35b3 | 588 | 15% | 0.67 | 0.20 (0.15) |
| 83084647 | 139 | 28% | 0.76 | 0.60 (0.28) |
| 8bc0c220 | 390 | 23% | 0.69 | 0.33 (0.23) |
| 9124740f | 223 | 20% | 0.79 | 0.39 (0.20) |
| 919fb76d | 28 | 18% | 0.61 | 0.45 (0.18) |
| a3d75cc3 | 326 | 8% | 0.69 | 0.12 (0.08) |
| ab4a91a5 | 327 | 8% | 0.95 | 0.55 (0.08) |
| b22eab3a | 67 | 57% | 0.34 | 0.48 (0.57) |
| b8bf186f | 367 | 3% | 0.61 | 0.06 (0.03) |
| bf647be4 | 319 | 6% | 0.70 | 0.12 (0.06) |
| c03b6b6c | 128 | 60% | 0.68 | 0.74 (0.60) |
| d006dd25 | 339 | 12% | 0.80 | 0.24 (0.12) |
| d1621b3d | 309 | 3% | 0.58 | 0.04 (0.03) |
| d69bd8e5 | 509 | 6% | 0.71 | 0.09 (0.06) |
| d85c76a6 | 64 | 53% | 0.45 | 0.51 (0.53) |
| d869eaea | 510 | 16% | 0.64 | 0.24 (0.16) |
| e761c500 | 82 | 46% | 0.43 | 0.42 (0.46) |
| e9700d51 | 15 | 33% | 1.00 | 1.00 (0.33) |
| f030febe | 376 | 53% | 0.53 | 0.53 (0.53) |
| f17813d0 | 332 | 10% | 0.78 | 0.27 (0.10) |
| f8fce67a | 50 | 34% | 0.95 | 0.92 (0.34) |
| fd49f89b | 97 | 22% | 0.94 | 0.83 (0.22) |

**Pooled (all held-out frames):** ROC-AUC **0.74**, PR-AUC **0.27** (base rate 0.14). With ~2 s smoothing: ROC-AUC 0.76, PR-AUC 0.29.

ROC-AUC 0.5 = guessing, 1.0 = perfect. PR-AUC is compared to the base rate (a guesser scores the base rate).
Caveat: few fights, and some clips are almost all attempt (few negatives), so per-fight AUCs are noisy or undefined (nan).
