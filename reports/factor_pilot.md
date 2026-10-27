# M2 pilot: can the computer see the choke factors? (2026-10-27)

Script: [research/attempt_clf/factor_pilot.py](../research/attempt_clf/factor_pilot.py), [output](../research/attempt_clf/factor_pilot_output.txt). Same features as the attempt detector (CLIP image features of the fighter crop plus 2–4 s of context). Every frame inside a labeled attempt is used (1,198 frames, 52 attempts, 29 fights), with the factor's labeled value at that moment as the target. Each fight is scored by a model that never saw it.

| Factor | Frame ROC-AUC | Attempt agreement with the label at 2 s | Always guessing the common value | Cohen's κ |
|---|---|---|---|---|
| Arm under the chin (vs over the jaw) | 0.57 | 65% | 76% | −0.04 |
| Figure-four (vs other grips) | 0.53 | 50% | 56% | −0.02 |
| Body triangle (vs hooks / less) | 0.61 | 63% | 62% | 0.17 |
| Defender 2-on-1 (vs not) | 0.43 | 50% | 67% | −0.25 |

**Verdict: 🔴 not yet. All are near chance, and none reaches the M2 bar (κ ≥ 0.4).** The features describe the whole picture ("two men on the ground"), not where an arm or a hand is. Note the contrast with the attempt detector (ROC-AUC 0.80): spotting a back attack is a whole-picture question, while the factors are small details.

**What could work (estimates):**
1. A small image model fine-tuned on frames cropped tightly around the heads and necks, once there are ~150 labeled attempts. That's laptop-CPU training on derived crops. UFC frames can't go to Kaggle.
2. Asking the labeler for a few seconds of extra "factor" labels at more moments per attempt (the G panel already does this) gives more training frames for free.
3. Until then, the overlay keeps the factors from labels and says so on screen.

## Next try, built (2026-10-27): factor model on tight head/neck crops
- `tools/save_neck_crops.py` saves 224×224 crops around the fighters' heads, 4 per second, inside every labeled attempt (`data/crops/`, local only). It runs before a labeled video is deleted, so the training set grows with every labeling batch.
- `research/attempt_clf/factor_neck.py` turns them into CLIP features (mirrored crops count as extra training data) and runs the same leave-one-fight-out test as above.
- Pipeline check on the 4 demo fights (561 crops, 10 attempts): runs end to end. Scores are meaningless at 4 fights ([output](../research/attempt_clf/factor_neck_output.txt)). The first real result comes after the 12 queued fights, and the M2 decision at ~150 attempts.
