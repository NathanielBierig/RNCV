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
