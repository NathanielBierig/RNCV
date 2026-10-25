# Attempt detector v2: adding a few seconds of context (2026-10-26)

Script: [research/attempt_clf/detector_v2.py](../research/attempt_clf/detector_v2.py). Raw output: [attempt_detector_v2_output.txt](attempt_detector_v2_output.txt). Same data and protocol as v1: 19 fights, 2,779 frames at 2 per second, about 23 minutes in total, and leave-one-fight-out (each fight is scored by a model that never saw it).

**The change:** v1 saw one frame at a time. v2 also sees the average image of the past ~2 s and ~4 s, plus how much the picture changed over the last 3 s. Everything it sees comes from the past, so it still works live.

| Variant | Frame ROC-AUC | PR-AUC (base rate 0.29) | Correct windows* | Any overlap | False alarms / min |
|---|---|---|---|---|---|
| v1: one frame, fighter crop | 0.70 | 0.47 | 8% | 75% | 0.49 |
| **v2: + context, fighter crop** | **0.74** | **0.55** | 8% | 78% | 0.43 |
| + context, whole frame + crop + bigger backbone | 0.73 | 0.52 | 22% | 69% | 0.61 |
| Replay-only (also looks 2–4 s ahead) | 0.75 | 0.56 | 11–14% | 47–67% | 0.24–0.49 |

\*Correct window = the detector's window starts within 2 s of the labeled start and covers mostly the same span. The app target is ≥ 80%.

**Honest read:**
- 🟢 Frame-level accuracy went up. ROC-AUC rose from 0.70 to 0.74 and PR-AUC from 0.47 to 0.55. Six context variants all landed at 0.73–0.75, so this isn't one lucky setting.
- 🔴 Timing did not improve. Only ~8–22% of attempts get a correctly placed window, and the variants that differ here are within noise (36 attempts). The detector still recognizes "back control + arms around the neck" as a whole exchange, not the moment a choke starts.
- The fix is more and different data: ~40 fights, plus rounds with back control but no choke (hard negatives). The one watched no-RNC clip (Pimblett–Leavitt) is no longer in `data/clips/`, so there are **zero** hard negatives right now.
- Kaggle can't help here: the features come from UFC frames, which never leave the laptop. CLIP features run on the CPU in a few minutes anyway.

## Tried and rejected: a separate "choke is starting" model
[onset_try.py](../research/attempt_clf/onset_try.py) ([output](../research/attempt_clf/onset_try_output.txt)) trained a model to tell the first 3 s of an attempt from the 1–8 s just before it. It scored **ROC-AUC 0.56**, close to guessing, and gating the detector with it did not raise the share of correct windows (≤ 8%). **Whole-image features can't see the moment the arm comes across the neck.** The timing needs a signal focused on the neck and arms, for example crops around the defender's head, or the head reticles the tracking layer already finds, plus more fights.

## Tried and rejected: head/neck crops
[extract_neck.py](../research/attempt_clf/extract_neck.py) built a square crop around the fighters' confident head keypoints. Alone it scored **ROC-AUC 0.69**; combined with the pair crop, **0.73**. Neither beats v2 (0.74), and correct windows stayed at ~14%, which is within noise. At 2 frames per second, with a 224-px CLIP input on broadcast-size heads, the arm-across-neck detail is still too small or too often hidden. **Verdict: the detector is data-limited, not feature-limited.** Next is ~40 fights plus hard-negative rounds, then re-test with `detector_v2.py`.
