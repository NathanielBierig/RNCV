# Attempt detector v2: adding a few seconds of context (2026-10-26, re-tested 2026-10-27)

## Re-test on 40 fights (2026-10-28)
11,333 frames, 14% inside attempts, ~65 min of no-attempt footage. Frame ROC-AUC **0.74–0.76** across variants (smoothed up to 0.77), PR-AUC 0.27–0.30 vs a 0.14 base rate. Any overlap with the attempt is 91%, but a correctly placed start only 9%, and there are 0.7–1.0 false alarms per minute. **The 0.80 on 29 fights was partly luck; ~0.75 is the honest level now.** Measured on far more no-choke grappling, false alarms are the main weakness. The demo shows the detector as is, and the overlay's numbers still start at the labeled attempt.

## Re-test on 29 fights, with 3× more no-attempt footage (2026-10-27)
The owner's 11 new fights came as full-fight videos, so each now contributes about 2 minutes of footage before the attempts (watched stretch only; compilations only near labeled attempts). Data: 6,248 frames, 19% inside attempts, about 42 minutes of no-attempt footage.

| Variant | Frame ROC-AUC | Smoothed | PR-AUC (base 0.19) | Correct windows | Any overlap | False alarms / min |
|---|---|---|---|---|---|---|
| v1 (one frame) | 0.78 | 0.80 | 0.38 | 17% | 76% | 0.57 |
| **v2 (+ context)** | **0.80** | **0.80** | **0.43** | 9% | 74% | 0.71 |
| v2, fewer false alarms (C 0.05) | 0.79 | 0.80 | 0.41 | 9% | 87% | 0.28 |

- 🟢 **Frame accuracy reached the M1 target (ROC-AUC 0.80).** It went 0.70 → 0.74 (context) → 0.80 (more fights and real negatives). More data helped far more than better features did, as predicted.
- 🔴 **Timing and false alarms are still short of the app target.** Correct windows are 9–17% (target ≥ 80%), and false alarms run 0.3–0.7 per minute (target ≤ 0.2). The false-alarm number is now measured on ~42 minutes, so it's more realistic than before, and worse.
- The manual "attempt starts" key stays for the demo. Next lever: rounds with back control but no choke.



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

## Check: video clock drift in .webm clips (2026-10-27)
OpenCV's "frame number ÷ fps" drifts from the real timestamp in variable-frame-rate `.webm` files: up to **9.9 s** on Oliveira–Gamrot, and 0.0 s on the `.mp4` clips. The labeler uses real timestamps, so frame labels in 11 older webm clips were partly misaligned. Extraction now uses real timestamps (`CAP_PROP_POS_MSEC`); Oliveira–Gamrot was re-extracted. The other webm videos were already deleted, so their effect was tested by leaving them out: ROC-AUC **0.789 without** them vs **0.798 with** them (smoothed 0.796 vs 0.803). The drift didn't hurt measurably (the clips are short), so they stay in. The same drift explained the "late overlay" in the Oliveira demo (fixed in `tools/mvp/demo.py`).

## Tried and rejected: camera cuts and shot types (2026-10-29)
[angles.py](../research/attempt_clf/angles.py) ([output](../research/attempt_clf/angles_output.txt)), 40 fights. Cut detection (357 cuts, about one per 16 s) with context kept within a shot, and zero-shot CLIP shot-type tags (wide, close-up, overhead, replay, crowd...) as extra features. Frame ROC-AUC 0.748–0.753 vs 0.750 for the baseline: **no gain**. Revealing: the 7 shot-type numbers *alone* reach **0.69**, so the detector mostly recognizes the *kind of shot* ("close-up of grappling") rather than the choke. That explains the failure on highlight reels. The deeper issue (owner, 2026-10-29) is that the fighters' orientation differs every time: left/right, rotated, half hidden. The fixes are mirrored/rotated training examples, which the neck-crop pipeline already uses (mirrors) and future extractions can store, and focusing on the neck region instead of the whole picture.
