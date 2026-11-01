# Automatic odds and timing, no hand labels (exploratory)

Input: image fingerprints from the first seconds of each attempt, tested on fights left out of training. Start times come from labels (best case). Hand-labeled model v0.8 for comparison: Brier 0.244 vs 0.256 at 2 s.

| Seconds seen | Fingerprint size | Attempts | Finish AUC | Brier vs guessing the average | Time error (median, s) vs guessing the median |
|---|---|---|---|---|---|
| 2 | 8 | 73 | 0.58 | 0.257 vs 0.257 | 3.4 vs 3.4 |
| 2 | 16 | 73 | 0.61 | 0.256 vs 0.257 | 3.3 vs 3.4 |
| 4 | 8 | 73 | 0.61 | 0.257 vs 0.257 | 3.3 vs 3.4 |
| 4 | 16 | 73 | 0.63 | 0.256 vs 0.257 | 3.3 vs 3.4 |
| 6 | 8 | 73 | 0.59 | 0.257 vs 0.257 | 3.3 vs 3.4 |
| 6 | 16 | 73 | 0.62 | 0.257 vs 0.257 | 3.2 vs 3.4 |

## Public stats only, no vision at all

Strikes and knockdowns in earlier rounds, plus the round number (74 attempts, fights left out of training): AUC 0.55, Brier 0.248 vs 0.256. Finish-enriched sample, so part of this may come from how fights were picked (`reports/damage.md`).

**How to read it:** image fingerprints don't beat guessing the average on Brier or on time, so the computer can't give useful odds or timing from pixels yet. An AUC around 0.6 with no Brier gain is not a usable signal.
