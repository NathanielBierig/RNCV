# What makes a UFC rear-naked choke finish? A pre-registered study, pilot report

*Pilot report, 2026-10-28. 73 labeled attempts from 42 fights. The confirmatory analysis runs at ~150 attempts; everything below is exploratory unless marked otherwise. Code, labels and figures: this repository. No UFC footage is included or redistributed.*

---

## Abstract

The rear-naked choke (RNC) is the most common submission in the UFC. Coaches agree on what makes it work: the choking arm under the chin, a locked grip, strong leg control, and beating the defender's hand fight. But no study has measured which of these details actually separates finished chokes from escaped ones in elite competition. We pre-registered three hypotheses before labeling any data: the arm under the chin raises the odds of a finish, strong leg control raises them, and a two-on-one hand fight by the defender lowers them. We then built a hand-labeling tool that records each attempt's state 2 seconds in, blind to the outcome.

This pilot covers 73 attempts from 42 men's UFC fights. The finish rate was higher with the arm under the chin (61% vs 40%), with a figure-four grip (68% vs 42% for one-armed chokes), with the choking hand hidden (75% vs 48%) and with the defender flattened out (66% vs 49%). Leg control showed no advantage per attempt (body triangle 46%, hooks 54%, one hook or none 68%), which we interpret as a measurement artifact of scoring single attempts rather than whole back exposures. Finished chokes took a median 9.6 seconds on the neck, consistent with the 9.0 s from lock to unconsciousness reported for 81 MMA choke-outs (Stellpflug et al., 2020).

An applied model combining expert priors with the labels gives a live finish probability. It is slightly better than a base-rate guess from the 2-second snapshot, and clearly better when it follows the position as it changes. An automatic attempt detector based on general-purpose image features reaches a frame-level ROC-AUC of about 0.75 on held-out fights. All intervals are wide at this sample size, and the confirmatory test is pending.

---

## 1. Introduction

Ask any jiu-jitsu coach why a rear-naked choke finished and you'll hear the same few details:
- **The arm went under the chin.** The forearm sits on the neck, not across the jawbone.
- **The grip was locked.** Usually a figure-four (the choking hand grips the other biceps).
- **The legs held the back:** a body triangle or both hooks.
- **The defender lost the hand fight.** A defender who peels the choking arm with both hands (a "two-on-one") often survives.

These beliefs come from experience, and experience is a biased sampler. We remember the spectacular finishes and forget the dozens of attempts that went nowhere.

**The question:** among UFC rear-naked choke attempts, which technical states at a fixed early moment are associated with the attempt finishing?

Measuring this needs three things the sport doesn't have:
- a definition of an "attempt" that two people would agree on;
- a way to code each attempt's state *before* knowing its outcome;
- a sample that includes failed attempts, not just the highlight-reel finishes.

This project builds all three, plus two applied tools: a live finish probability overlay and an automatic attempt detector.

**What is known about timing.** Stellpflug et al. (2020) timed 81 choke-outs in MMA and found an average of 9.0 seconds from a locked choke to unconsciousness (95% CI 8.3–9.9 s; RNC 8.9 s). Carotid compression, not airway closure, drives the loss of consciousness, which is why a choke over the jawbone, which shields the carotids, rarely puts anyone out. No published study compares grip types or leg control as predictors of the finish. The project's evidence review ([EVIDENCE.md](../../research/priors_evidence/EVIDENCE.md)) documents what exists and what doesn't.

## 2. Pre-registration

The study plan ([PREREG.md](../../research/rnc_science/PREREG.md)) was frozen at version 1.0 before any pilot labeling. Changes since then are dated amendments, never silent edits.

**Hypotheses** (confirmatory, primary model, at most 4 degrees of freedom):

| # | Factor at 2 s | Prediction |
|---|---|---|
| H1 | Choking arm under the chin (vs over the jaw) | Higher odds of a finish |
| H2 | Body triangle or both hooks (vs less) | Higher odds of a finish |
| H3 | Defender two-on-one hand fight | Lower odds of a finish |
| — | Time left in the round | Adjustment only |

**Decision rule:** a hypothesis is *supported* if its 95% interval excludes "no effect" in the predicted direction, *contradicted* if it excludes it in the opposite direction, and *inconclusive* otherwise. Inconclusive is a valid, reportable result.

**Amendments so far:**
- A1: men's divisions only.
- A2: an upper-body control field and a timestamped change log of the position, for descriptive and hazard analyses only.
- A3: the per-fighter cap counts attacking rounds, not attempts.
- A4: the cap was raised from 3 to 5 attacking rounds.

**Why pre-register a sports question?** With dozens of possible factors and a small sample, some factor will always look important by chance. Fixing the hypotheses and the test in advance is what separates a finding from a pattern found after the fact.

## 3. Data

**Population:** men's UFC fights, 2018–2026, with at least one rear-naked choke attempt.

**Sampling (hybrid):**
- **Finish list.** Attempts from fights that ended by RNC (677 such finishes on ufcstats). Choosing by outcome distorts the *overall* finish rate but keeps comparisons *between* factors valid, which is what the hypotheses test.
- **Failure rounds.** Rounds flagged with submission attempts where the choke didn't finish.
- **Random subset (planned).** About 10 fully watched fights drawn at random, for an honest base rate.

**Every** RNC attempt in a watched round is labeled, including failed attempts before a finish. Each row records how it was found (`found_via`), and the analysis adjusts for it.

**Pilot sample:** 73 attempts from 42 fights (72 after excluding one bell-censored attempt). 64 came from finish-list fights and only 8 from failure rounds. **The sample is heavily finish-enriched,** so the overall finish rate here (56%) is far above the real-world rate. Only comparisons between factor values are meaningful.

**Footage:** only official UFC uploads and licensed broadcasters, watched locally. Videos are deleted after processing. Only derived data (timestamps, labels, image features) is kept, and no pixels are ever published.

## 4. Coding

**What counts as an attempt** ([LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md)):
- the attacker has back control;
- the choking arm is across the neck (under the chin or over the jaw);
- the second hand is working to lock it.

A re-start after less than 2 seconds without losing the back is the same attempt.

**The landmark.** Factors are coded at **2 seconds after the attempt starts**. The labeling tool pauses the video there and shows a fixed panel of questions before the outcome is visible. The panel covers arm position, grip type, leg control, the defender's two-on-one, chin tucked, choking hand hidden, defender flattened, and more. Changes after the landmark are logged with timestamps (a second panel opened with the G key).

**Outcomes:**
- **Success:** tap, referee stoppage or unconsciousness.
- **Failure:** escape or the attacker abandoning the choke.
- **Censored:** the round ends (bell).

**Reliability:** a second rater will code at least 30 attempts. Any factor with Cohen's κ below 0.4 will be reported as "not reliably codable from broadcast", whatever its effect. 🔴 *Not done yet.*

**Quality control:** an automated QA script flags overlapping attempts, impossible round times, mismatches with official finish times, out-of-scope fights and cap violations. The pilot data passes with zero red flags.

## 5. Analysis plan (confirmatory, at ~150 attempts)

**Primary analysis:**
- Firth-penalized logistic regression (stable with small samples and rare combinations).
- Profile-likelihood 95% intervals, reported as odds ratios.

**Sensitivity analyses:**
- a cluster bootstrap by attacker;
- unclear values coded as each extreme;
- attempts with camera cuts removed.

**Secondary analysis:** a discrete-time hazard model (second by second, finish vs escape, with the bell as censoring).

The script ([prereg_analysis.py](../../research/rnc_science/prereg_analysis.py)) is written and tested on simulated data. Its 95% intervals covered the true values 95–100% of the time. **Power is sobering:** at 150 attempts, a large effect (odds ×4, as expected for H1) is detected almost always, but a moderate one (odds ×2) only about 42% of the time. Moderate effects may honestly come out inconclusive. The script refuses to run on real data before the target sample.

## 6. Pilot results (exploratory)

**Finish rate by factor at the 2-second landmark** (72 attempts; 95% Wilson intervals). Source: [findings_pilot.md](../../reports/findings_pilot.md).

| Factor | Value | Attempts | Finished | 95% interval |
|---|---|---|---|---|
| Arm | under the chin | 56 | 61% | 48–72% |
| | over the jaw | 15 | 40% | 20–64% |
| Grip | figure-four | 37 | 68% | 51–80% |
| | palm / gable / wrist pull | 10 | 50% | 24–76% |
| | one arm / short choke | 19 | 42% | 23–64% |
| Legs | body triangle | 24 | 46% | 28–65% |
| | both hooks | 26 | 54% | 35–71% |
| | one hook / none | 22 | 68% | 47–84% |
| Defender two-on-one | yes | 23 | 57% | 37–74% |
| | no | 49 | 55% | 41–68% |
| Choking hand hidden | yes | 20 | 75% | 53–89% |
| | no | 52 | 48% | 35–61% |
| Defender flattened | yes | 29 | 66% | 47–80% |
| | no | 43 | 49% | 35–63% |

**Adjusted effects.** Each factor's odds multiplier with the others held fixed: the applied model of section 7, expert priors plus labels.

![Odds multipliers per factor](../media/effects.png)

**Reading the pilot:**
1. **H1 (arm under the chin) points the predicted way** in both views: raw 61% vs 40%, adjusted ×4.6.
2. **The grip matters, in the coach's order.** Figure-four > other locks > one arm. Adjusted: figure-four ×3.0, other locks ×2.0 vs one arm.
3. **The hidden hand and a flattened defender look important** (×2.0 and ×2.4 adjusted). Neither is a pre-registered hypothesis, so both are hints for a future study.
4. **H3 (two-on-one) shows no raw difference (57% vs 55%) but a negative adjusted effect (×0.56).** Two-on-ones happen more in the deep, locked positions that finish anyway. Once position is accounted for, the hand fight costs the attacker about half the odds.
5. **H2 (leg control) points the *wrong* way per attempt.** We think this is a real limitation of scoring single attempts, not evidence that legs don't matter:
   - Strong leg control keeps the attacker on the back, so they get several attempts per round, and the early ones fail before one lands.
   - Many quick finishes come right after a knockdown, onto a hurt defender, before any hooks are in.

   "Hurt before the back take" isn't labeled yet. A model of whole back exposures, rather than single attempts, would test the retention effect directly.

**Time on the neck.** Finished chokes took a median **9.6 s** (middle half 6.5–12.9 s), matching the 9.0 s from lock to unconsciousness in Stellpflug et al. (2020). Failed attempts also lasted a median 9.6 s (6.3–15.1 s). Duration alone doesn't predict the outcome. Position does.

**Re-attacks.** First, second and later attempts in a round finished 57%, 56% and 50% of the time. This can't be tested fairly yet: in a finish-list round, the finish is always the last attempt by construction.

## 7. Applied model: a live finish probability

Separate from the confirmatory study, a live model estimates the chance that *this* attempt finishes, given the position visible now.

**How the knowledge is built:**
- **Expert scenario cards.** The owner (a BJJ practitioner) gave a finish-probability bucket for about 10 scenarios. A published-evidence review and an AI coach review added cards. Each card counts as 2–3 pretend attempts.
- **The labels then update every weight** through a Bayesian logistic model.

**The defender's "HP"** is a separate running total, not a forecast. It is a blood-flow dose that drains with squeeze strength (a locked figure-four under the chin about 0.9, one arm 0.45, over the jaw 0.05) and empties after 9 s at full squeeze (the Stellpflug average).

**Validation.** Leave-one-fight-out: every fight is scored by a model that never saw it.
- At the 2-second landmark, model v0.8 scores a Brier score of 0.245 vs 0.254 for always guessing the average. The difference is within noise.
- Following the position as it changes (every second), it scores **0.224 vs 0.254**.
- Six model variants were tested and all are reported ([MODEL_SPEC §4g](../MODEL_SPEC.md)). A re-attack term and a time-left adjustment made it worse.

![Calibration on held-out fights](../media/calibration.png)

**Calibration.** When the model says ~80%, those attempts finished ~80% of the time. In its lower bins it is too pessimistic: its 20% bin finished about 45% of the time. **The model's value is in tracking how a choke develops, not in judging it from a snapshot.**

## 8. Automatic detection (appendix)

**Why not skeletons?** Pose models turn video into skeletons, but in a back take the bodies are tangled. A manual review found both fighters' skeletons correct in only **4 of 48** frames. So the detector skips skeletons.

**How it works:**
- Each frame (2 per second, cropped to the fighters) is turned into a general-purpose image fingerprint (CLIP).
- The fingerprint is combined with the average of the past 2–4 seconds.
- A logistic regression learns "inside an attempt or not".

**Results on held-out fights:**
- The frame-level ROC-AUC rose from 0.70 to 0.80 as fights were added, then settled at **~0.75** on 40 fights as far more no-choke grappling entered the test (about 65 minutes).
- It recognizes a back attack but not the exact second the choke starts (correct within 2 s for only ~9% of attempts), with 0.7–1.0 false alarms per minute.

**Tried and rejected:**
- a separate "choke is starting" model (AUC 0.56);
- head and neck crops for the detector;
- a first attempt at recognizing the factors themselves (arm, grip, legs, two-on-one) from the same image fingerprints, which reached near-chance agreement with the labels (κ ≤ 0.17).

A dedicated factor model on tight neck crops is being built as labels accumulate. Full reports: [attempt_detector_v2.md](../../reports/attempt_detector_v2.md), [factor_pilot.md](../../reports/factor_pilot.md).

## 9. Limitations

- **Small, finish-enriched sample.** 72 attempts, 64 from finish-list fights. Intervals are wide and the overall finish rate is inflated. Failure rounds and the random subset are the priority.
- **Single rater so far.** No reliability (κ) yet.
- **Broadcast views hide the hands.** Some factors are coded "unclear", and camera cuts hide parts of attempts.
- **Per-attempt scoring can't credit position retention** (see H2).
- **Unlabeled confounders.** A knockdown before the back take, fatigue, the cage.
- **Expert priors.** The applied model uses expert and AI-coach priors. They are weighted lightly and disclosed, but they are opinion, not data.
- **Supply.** Official and broadcaster videos cover only part of the target sample. Reaching 150 attempts may need other legal viewing routes.

## 10. Ethics and data

No UFC footage is stored in the repository, uploaded or shared. Clips are watched locally and deleted after processing. Only timestamps, labels and numeric features are kept. A release check scans the repository and its full history for video files and secrets before any public release.

## References

- Stellpflug SJ, Menton TR, Dummer MF, Menton WH, Corry JJ, LeFevere RC (2020). Time to loss of consciousness from locked chokes in mixed martial arts. *International Journal of Performance Analysis in Sport* 20(4):720–728. doi:10.1080/24748668.2020.1780873 (title paraphrased; see the DOI). Also: Stellpflug (2020), UFC choke finishes 1993–2020, PMID 33347362.
- Firth D (1993). Bias reduction of maximum likelihood estimates. *Biometrika* 80:27–38.
- Radford A, et al. (2021). Learning transferable visual models from natural language supervision (CLIP). *ICML.*
- Project documents: PREREG.md, FACTORS.md, LABEL_SCHEMA.md, MODEL_SPEC.md, EVIDENCE.md, COACH_REVIEW.md.
