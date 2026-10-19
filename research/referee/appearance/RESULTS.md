# Referee removal by appearance: results (2026-10-19, first pass)

Eval set: `research/referee/eval/labels.csv` (128 frames, 3 clips, 79 non-tiny referee detections, labeled by eye). Scripts: `features.py` (CLIP ViT-B-32 laion2b + skin cues for every stride-5 detection), `evaluate.py` (this table). Learned methods are leave-one-clip-out (LOCO). Threshold: referee score > 0.5 is dropped before `select()`'s overlap-pair rule.

- **Both fighters kept** = frames with 2+ labeled fighters where the 2 kept people are both fighters.
- **Referee kept** = frames with a visible referee where `select()` still keeps the referee.

| Method | AUC | Precision | Recall | Fighters flagged | Both fighters kept | Referee kept | Both kept per clip (gsp / pantoja / sterling) |
|---|---|---|---|---|---|---|---|
| Baseline: overlap pair (current select) | – | – | – | – | 25/30 (83%) | 46/79 (58%) | 9/12 / 6/7 / 10/11 |
| a. CLIP zero-shot | 0.88 | 0.68 | 0.38 | 0 | 25/30 (83%) | 27/79 (34%) | 9/12 / 6/7 / 10/11 |
| a. + track vote | 0.91 | 0.67 | 0.30 | 1 | 24/30 (80%) | 34/79 (43%) | 9/12 / 6/7 / 9/11 |
| a'. CLIP linear probe (LOCO) | 0.86 | 0.56 | 0.76 | 21 | 22/30 (73%) | 12/79 (15%) | 5/12 / 6/7 / 11/11 |
| a'. + track vote | 0.86 | 0.58 | 0.76 | 12 | 18/30 (60%) | 13/79 (16%) | 6/12 / 2/7 / 10/11 |
| **b. Skin rule (`referee.py`)** | 0.88 | 0.73 | 0.77 | **1** | 25/30 (83%) | **8/79 (10%)** | 9/12 / 5/7 / 11/11 |
| b. + track vote | 0.88 | 0.65 | 0.67 | 5 | 22/30 (73%) | 15/79 (19%) | 9/12 / 3/7 / 10/11 |
| **b'. Skin features + logistic (LOCO)** | **0.94** | 0.72 | **0.81** | **0** | **26/30 (87%)** | 10/79 (13%) | 9/12 / 6/7 / 11/11 |
| b'. + track vote | 0.92 | 0.62 | 0.76 | 10 | 21/30 (70%) | 14/79 (18%) | 10/12 / 2/7 / 9/11 |
| a+b average | 0.88 | 0.71 | 0.46 | 0 | 25/30 (83%) | 26/79 (33%) | 9/12 / 6/7 / 10/11 |
| a+b average + track vote | 0.88 | 0.76 | 0.56 | 1 | 24/30 (80%) | 18/79 (23%) | 9/12 / 6/7 / 9/11 |

## Reading it (honest)
- **The skin/clothing cue wins.** It cuts "referee kept" from 58% to 10–13% and flags 0–1 real fighters. Dark-skinned Sterling is not dropped, because the cue uses chroma, not darkness. Sterling clip: 11/11.
- **CLIP zero-shot is too timid** (recall 0.38). The linear probe catches referees but flags 21 fighters. Not worth the torch dependency.
- **Track voting hurts in this version.** My IoU+embedding tracker merges the referee with fighters when they touch (pantoja drops to 2–3/7). This isn't a verdict on voting itself: the tracker needs fixing (e.g. vote only on tracks with a stable box, or use the 2-slot fighter tracker).
- "Both fighters kept" barely moves (83 → 87%). Most remaining misses are frames where RTMO never detected the second fighter, which a referee filter can't fix.
- Small set: 3 clips, 2 referees. The LOCO logistic (b') weights were fitted on 2 clips. Its 0.94 AUC is the best estimate here, but its CIs are wide.

## Recommendation
Port `referee_score()` from `research/referee/appearance/referee.py` (no new dependencies, OpenCV only) into `src/two_fighters.select`: with 3+ candidates, drop people with score > 0.5 first, then apply the overlap-pair rule. Optionally swap in the b' logistic weights (fit on all 3 clips) later.

## Not done yet (usage limit reached)
- Failure-example images were not saved.
- The track-vote fix was not attempted.
- b' weights were not exported into `referee.py`.
