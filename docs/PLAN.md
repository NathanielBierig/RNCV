# UFC Submission CV — Project Plan

> Owner: you. Code, environment and `data/` belong to the build session (`build-phase2`). This document is the plan.
> Every time, accuracy and compute figure here is an **estimate**, unless a source is linked.

## Chosen direction (2026-10-18)

**Core: "Science-based RNC."** Which details of a rear-naked choke predict a finish? Arm under the chin vs on the jaw, hooks vs body triangle, flattening the defender, the defender's hand fighting, round, and time held. Each effect is reported with a confidence interval.
**Showcase: the live overlay.** It shows the finish probability *plus the factors driving it* right now.

What this changes in the plan:
- **Phase 3:** the labels must record each factor, coded blind at the 2-s landmark; the code book is [FACTORS.md](../research/rnc_science/FACTORS.md). These are the science variables, so labeling them carefully matters more than the attempt count alone.
- **Phase 5:** the model must be **interpretable first** (logistic regression → odds ratios with CIs), and predictive second.
- **Phase 6:** the overlay shows the top factors along with the probability.
- Study design lives in `research/rnc_science/` and the renderer in `tools/overlay/`, both owned by the main session. This plan only sets the interfaces.

## 0. One-paragraph summary

You'll build a pipeline that runs on keypoints. It takes the **pose** of both fighters (17 body keypoints each), works out their **position** (back control, mount and so on), detects **rear-naked choke (RNC) attempts**, and outputs a **finish probability** that updates while the attempt unfolds. That probability gets drawn on recorded clips. The models are small: gradient-boosted trees and tiny temporal networks, so they train on a CPU or a free GPU. Data is the expensive part. You have to label about 150 RNC attempts from UFC fights yourself, and that labeling is the **critical path**: the chain of tasks that sets the earliest possible finish date. The biggest technical risk is pose quality on broadcast ground fighting. A small experiment in week 2 tests that risk, before you spend labeling hours.

## 1. Key terms (defined once)

| Term | Meaning |
|---|---|
| Keypoints / pose | (x, y, confidence) for 17 COCO body joints per person |
| Tracker | Keeps the same ID on the same fighter from frame to frame |
| Group split | A train/test split where every frame of a fight (or sequence) lands on the same side. Without it, the test score is fake. |
| Macro-F1 | F1 computed for each class, then averaged. Rare classes count as much as common ones. |
| PR-AUC | Area under the precision–recall curve. More honest than accuracy when positives are rare. |
| ROC-AUC | The probability that a random success gets a higher score than a random failure. 0.5 = random. |
| Brier score / calibration | Measures whether a "70%" prediction actually comes true about 70% of the time |
| Leakage | When the model gets information from the future or from the test set. Example: predicting "success" 0.2 s before the tap. |
| Event-level F1 | A detected attempt counts as correct if it overlaps a labeled attempt by temporal IoU ≥ 0.3 (IoU = overlap ÷ union) |

## 2. Recommended stack (license-checked)

| Need | Pick | License | Why |
|---|---|---|---|
| Pose (main) | [rtmlib](https://github.com/Tau-J/rtmlib) with **RTMO-m** (one-stage, built for crowded scenes) or RTMPose + detector | Code Apache-2.0; **weights: check** | ONNX runs on a CPU for small tests and on a Kaggle GPU for bulk work. The code license is clean, but the pretrained weights were trained on several public pose datasets, some of them research-only, so check the weights' terms before any commercial use (critique #16). |
| Pose (comparison) | Ultralytics YOLO11-pose | AGPL-3.0 ([commercial license needs a quote](https://www.ultralytics.com/license)) | Easiest API. Fine for open-source hobby work; it blocks closed-source profit. |
| Tracking | `supervision` ByteTrack (Roboflow) | MIT (verify in repo) | Simple. There are only 2 fighters, so add a "color of shorts" check to fix ID swaps. |
| Fighter vs referee | Fine-tune a detector on [FightersMMA](https://universe.roboflow.com/teamsilver/fightersmma-9vudg) | CC BY 4.0 | The class is `mma_fighter` only, so the referee is excluded automatically |
| Camera-cut detection | PySceneDetect | BSD-3 (verify) | Resets the tracker at every cut |
| Classifiers | scikit-learn, LightGBM | BSD / MIT | CPU-friendly and strong on small data |
| Temporal models | PyTorch 1D-CNN/GRU. Upgrade path: [ActionFormer](https://github.com/happyharrycn/actionformer_release) | BSD / MIT | Tiny, because there are fewer than 1k events |
| Position data | [VICOS BJJ](https://vicos.si/resources/jiujitsu/) | CC BY-NC-SA 4.0 | Non-commercial only. Anything derived from it inherits NC. |
| Labeling | Start with a CSV plus a video player that shows milliseconds (mpv/VLC). Move to Label Studio if it gets painful. | — / Apache-2.0 | Simplest thing that works |
| Fight stats | Scrape ufcstats.com politely ([ufc-scraper docs](https://ufc-scraper.readthedocs.io/en/stable/_sources/ufcstats_tables.rst.txt)) or use [Kaggle UFC data](https://baselight.app/u/kaggle/dataset/rajeevw_ufcdata) | Facts; check each dataset's license | Gives finish method, round and time, plus submission attempts per round |

## 3. Compute budget (estimate)

| Phase | Laptop CPU | Kaggle GPU h | Notes |
|---|---|---|---|
| 2 | Classifier on the provided keypoints | 2–4 | Re-extracting pose for 120k VICOS images |
| 3 | Labeling | 3–6 | Pose plus position classifier over about 100 rounds, for pre-labeling |
| 4 | Training | 1–3 | Features are cached, so GPU use is mostly pose extraction |
| 5 | Training | 0–1 | Trees and logistic regression; a CPU is enough |
| 6 | — | 1–2 | Rendering demo clips |
| **Total** | | **about 10–16 h** | Well under one week of Kaggle quota |

---

## Phase 1 — Resource search ✅ done
Results are in the chat summary. Main conclusion: nothing public covers submission attempts or their outcomes in MMA, so the labeled RNC set will be original work.

---

## Phase 2 — Pose + ground-position classifier (VICOS)

**Goal:** Classify 18 position classes (10 positions × which athlete is on top) from the keypoints of two people. The model is also a tool: its **"Back" class** becomes the RNC candidate finder used in Phase 3.

**Simplest approach**
1. CPU: load `annotations.json` (provided keypoints) and build features: normalized coordinates of both athletes, distances and angles between them, and confidence scores. Train a LightGBM baseline.
2. Kaggle: re-run *your* pose model (RTMO-m) on the VICOS images and retrain. **Why:** at inference time your keypoints come from your model, not theirs, so the training keypoints should too.
3. Optional: a temporal model over a 1-second window (1D-CNN/GRU), which smooths frame-to-frame flicker.

| | |
|---|---|
| Inputs | `annotations.json`, `images.zip` (only needed for step 2) |
| Outputs | `position_model.pkl`, per-frame position probabilities, a confusion matrix |
| Eval | **Time-block folds with all cameras together** (`src/vicos_data.time_block_folds`): 5 contiguous frame blocks per sequence, with a ±300-frame purge gap between train and test. ~~Leave-one-sequence-out~~ doesn't work, because each of the 6 sequences drills only 2–4 positions (e.g. seq 5 = back only), so a held-out sequence's classes never appear in training. Splitting by video leaks, because the 16 videos are 6 sequences × up to 3 synced cameras showing the same moment. Metrics: macro-F1, balanced accuracy, per-class recall. |
| Caveat | Same athletes, same session, so **the scores are optimistic**. VICOS can't measure generalization to new athletes. Only Phase 3+ UFC data split by fight can, so judge the position model's real value on the first labeled UFC rounds (does "Back" fire during real back control?). |
| Critique findings (#1, #13) | **"Back" exists in only one VICOS sequence** (one session, one pair of athletes), and every other sequence drills one position family, so position is confounded with session. Measured: macro-F1 0.447, Back recall 0.64. Both are below the gate even in this optimistic setup. The model also isn't **symmetric in athlete order**: swapping pose1/pose2 changes the result (F1 0.59 vs 0.45), while UFC tracker IDs are arbitrary. Fixes (build-phase2): train with swap augmentation (swap the poses *and* the 1/2 label suffix), or predict an order-free position plus a separate "who's on top/back" head. Expect the VICOS-based pre-labeler to be weak, and compare it against the geometry rule ("chest against back") on UFC frames in the week-2 stopwatch test. |
| Baseline to beat | Always predicting the majority class, and a k-NN on raw keypoints |
| Risks | Only 6 sequences and the same few athletes, so the model may memorize body shapes. The keypoints aren't guaranteed correct. Gym footage ≠ cage footage. |
| Time (est.) | 6–10 h |
| **Go/no-go** | Two steps. (1) VICOS time-block folds: macro-F1 ≥ 0.6 and "Back" recall ≥ 0.8. This is a sanity check only, since the scores are optimistic. (2) **The real gate:** on the first 10 labeled UFC rounds, "Back" segments cover ≥ 80% of your labeled RNC attempts (that number decides whether pre-labeling works). Below that, use plain tracking and "one fighter's chest against the other's back" geometry rules for candidate finding instead. |

### Phase 2b — Broadcast pose smoke test (de-risking spike, week 2)
Run pose plus tracking on **3–5 short UFC ground clips** (at least one RNC each). Watch the overlay and count frames where both fighters' heads and arms are plausible.
- **Go:** ≥ 60% usable frames during back control (est. threshold).
- **No-go:** Fallback A is to fine-tune RTMO on 200–300 hand-corrected frames. Fallback B is appearance features (frozen DINOv2 image embeddings, Apache-2.0) instead of keypoints. Decide before Phase 3 labeling hours go in.

---

## Phase 3 — UFC RNC dataset (labeling)

**Goal:** About 150 labeled RNC attempts with start/end times and outcomes, from about 100 fights. This is the asset nobody else has.

### 3.1 Footage (decided 2026-10-18: UFC only; see [FOOTAGE.md](FOOTAGE.md))
- **Labeling** (timestamps, outcome, factors, style tags) is done from legitimate streams (UFC Fight Pass, UFC's official free fights on YouTube). No copies are needed.
- **Pose work** (2b, 4, 5b, 6) uses private local clips of single attempts, kept on the laptop and run on the CPU. This is a personal-research risk the user accepts knowingly (not legal advice). Raw video never goes to git, Kaggle, cloud drives or social media.
- **Public output is derived only:** labels, stats, plots, and skeleton-only renders on a blank background. Overlays on real UFC frames stay private (shown live in interviews). No gym footage or other promotions for now.

### 3.2 Finding candidates from stats
1. Scrape ufcstats.com fight pages and get: `method`, `round`, `time`, and per-round `sub_att` and `ctrl` (control time) for each fighter.
2. **Successes:** `method` contains "Rear Naked Choke" → the exact round and clock time of the finish. Find the attempt start by scrubbing backward about 60 s.
3. **Failure candidates:** rounds with `sub_att ≥ 1` and high control time, in fights that did *not* end by RNC in that round. You scrub those rounds by hand, so failures cost more labeling time. Note that a `sub_att` count can be any submission type.
4. **Prior:** no reliable per-attempt finish rate exists. The often-quoted "41%" (Fightnomics, via a now-dead CagePotato link) has an unknown denominator, so **don't use it** (critique #15). RNC accounts for [about 49% of UFC choke finishes](https://combatsportslaw.com/2020/12/26/physician-reviews-and-analyzes-all-choke-submissions-in-ufc-history/) (through 2020), but that's a share of finishes, not a rate. The real ratio comes from the pilot (5).
5. **Sampling bias (critique #3).** Successes come from a complete list, while failures only come from rounds a scorer flagged. Rounds that ended in a submission were excluded, even though about 128 of 693 RNC finishing rounds also contain earlier attempts. So the success:failure ratio in the labels reflects *how they were found*, not how RNCs behave. Fixes:
   - Sample **fights**, not outcomes. Pick a seeded random set of fights from successes ∪ candidates, then label **every** RNC attempt in every labeled round, including failed attempts earlier in a round the attacker later finished.
   - Record `found_via` (`success_list` / `candidate_round` / `same_round_as_finish`) so the analysis can weight or stratify by it.
   - Only report a "finish rate" from the fight-sampled set.


### 3.3 AI pre-labeling (saves your hours)
Run pose → tracker → Phase 2 position model over every candidate round. Output **back-control segments** longer than 3 s as a review list, each with a start time. You review only those segments, plus a 10 s buffer, instead of whole 5-minute rounds. Target: under 4 minutes of review per round (est.).

### 3.4 Label schema: one source of truth

The earlier draft of this section disagreed with the labeling files on the start rule, the escape rule and the outcome codes (critique #4). **The authoritative definitions are now:**
- **Attempts:** [`phase3_labels/LABEL_SCHEMA.md`](../phase3_labels/LABEL_SCHEMA.md). Columns are `fight_id, round, attempt_start_s, attempt_end_s` on the round clock, plus `attacker, defender, outcome, camera_cut_flag`. Outcome codes are `tap, ref_stop, unconscious, escape, position_change, bell`. Start requires back control *and* the arm across the neck *and* the second hand locking.
- **Science factors: [`research/rnc_science/FACTORS.md`](../research/rnc_science/FACTORS.md) is the single code book** (factor names, codes, style tags, landmark rule). PLAN keeps no code list of its own (critique S12). If FACTORS disagrees with LABEL_SCHEMA, FACTORS wins.
- **Code:** `tools/eval_harness/horizons.normalize_labels()` reads that schema and **fails loudly** on unknown columns or codes.

Rules this plan adds on top:
- **`bell` is censoring, not failure.** The choke was still on when time ran out, so the harness leaves it out of finish/fail scoring by default and reports the count. In the hazard analysis (5a) it's a censored observation.
- **`position_change` into another submission that finishes:** add `notes: chained_finish`. The science analysis keeps these separate, as a sensitivity check.
- **Factor states over time:** if FACTORS.md adopts a timeline (a row per state change: `attempt_id, t_s`, factor values), the live predictor uses it. Otherwise only per-attempt values exist, and 5b must estimate factor states from pose.
- **Never model inputs:** `seconds_to_lock`, "deepest point" values, the outcome and the end time. These are enforced by `LEAKY_COLUMNS` in the harness.
- **Agreement:** κ is checked per factor as well as for the outcome. A factor below κ 0.6 is reported as unreliable, not interpreted.

**Quality check:** two weeks after labeling the first 20 attempts, re-label them blind. Target Cohen's κ (chance-corrected agreement) ≥ 0.8 on outcome, and start-time differences under 1 s. If you miss that, tighten the rules before going further.

### 3.5 Targets

| | Count (est.) |
|---|---|
| Minimum viable | 100 attempts (≈40 success / 60 fail), ≥ 70 fights |
| Target v1 | **150 attempts, ≥ 100 fights** |
| Locked test set | About 20% of fights, chosen by a frozen hash rule (`splits.lock_test_groups`), so fights labeled late join the test set at the same rate as pilot fights (critique #10). Never tuned on. |
| Negatives for Phase 4 | Back-control segments with no attempt, which come free from pre-labeling |
| Labeling time | **Measure it in the pilot** (15 attempts from randomly chosen fights, logging `search_min`/`label_min`). Rough estimate: successes about 15–20 min each, while failures cost 2–3× more because candidate rounds have to be scrubbed (critique #14). Plan for **50–80 h** until the pilot says otherwise. |

| | |
|---|---|
| Risks | Footage access. Failure attempts are slow to find. Your rules drift over time. Replays get mistaken for live action. |
| Time (est.) | 30–45 h, spread over about 5 weeks |
| **Go/no-go** | ≥ 100 usable attempts *and* κ ≥ 0.8. Otherwise stop and fix sourcing before Phase 4. |

---

## Phase 4 — RNC attempt detection

**Goal:** Find RNC attempts in a round: start/end segments with a confidence score.

**Simplest approach**
1. Features for each frame: position probabilities (Phase 2), plus RNC geometry. Examples: distance from the attacker's wrists and elbows to the defender's neck (between nose and shoulder midpoint), the attacker's chest behind the defender's shoulders, defender hands near the attacker's wrist, and keypoint confidence.
2. Windows: 2 s windows, stepping 0.5 s. Label = overlaps an attempt. Model = LightGBM, then a small 1D-CNN.
3. Post-processing: hysteresis thresholds (turn on at 0.6, off at 0.4) and a minimum length of 1.5 s, which yields segments. Reset at every scene cut.

| | |
|---|---|
| Eval | `GroupKFold` by `fight_id` on the training fights, with `purge_shared_fighters` (the same fighter never appears on both sides, critique #9), then a single run on the locked test set. Metrics: event-level F1 at tIoU ≥ 0.3 within fight + round, PR-AUC per window, median start-time error, and **false alarms per hour of *exhaustively* labeled rounds**. Label 10–15 full rounds end-to-end for this, because candidate-only review can't measure false alarms (critique #11). |
| Baselines | "Back control longer than 3 s = attempt" rule, using Phase 2 output only |
| Risks | Occlusion hides the choking arm. Negatives are rare and close to the positives (hand-fighting on the back looks like an attempt). Replays count as duplicates (detect them, or drop them using `has_replay` ranges). |
| Time (est.) | 12–18 h |
| **Go/no-go** | Event F1 ≥ 0.5 and fewer than 3 false alarms per fight-hour on the locked test set (est. targets). Below that, use Phase 4 as a pre-labeler only and run Phase 5 on your hand-labeled segments. That still makes a valid demo. |

---

## Phase 5 — RNC science + live finish probability

**Goal 1 (core, science):** Estimate how much each RNC detail changes the chance of a finish, with confidence intervals.
**Goal 2 (showcase):** At each moment *t* seconds into an attempt, output P(finish) using only frames up to *t*, plus the factors pushing it up or down.

### 5a. Interpretable factor model (primary analysis), revised after critique §B

- **Pre-register first, with a timestamp (S13).** Write `research/rnc_science/PREREG.md` (main session): hypotheses, codings, landmark, model, CI method and decision rules. Commit it **before the 15-attempt pilot**, so the git history proves it came first.
- **Landmark design instead of "first 3 s or deepest point" (S1, S2).** Score each factor **at a fixed landmark** L = 2 s after the attempt start, among attempts still ongoing at start + L + 2 s. This matches the harness's eligibility rule.
  - No "deepest point" and no "ever reached state X" codings. Those leak the outcome, and longer attempts get more chances to reach a state.
  - **No `time held` predictor.** Duration is a *result* of the outcome. Time enters only through the landmark, and through the hazard model's time axis.
- **Predictor budget (S4, S10).** Count degrees of freedom, not names. Real finishes may be fewer than 60, so the **primary** model gets at most **4 df**: `arm` (under_chin vs not), `lower_body` (body_triangle or both hooks vs less), `defender_two_on_one`, and `round_time_left` (adjusts for bell censoring, S14). `flattened`, grip and round are **secondary/exploratory**, reported as such. A power table at realistic prevalence (e.g. a factor in 20% of attempts) goes in PREREG, which makes clear that small effects are undetectable.
- **No tautological factors (S3).** `defender_turning` and `arm = off` are part of the escape definition, so they're excluded as predictors. They can only describe *how* attempts fail.
- **Model and CIs (S5).** **Firth logistic regression** (removes small-sample bias) with **profile-likelihood 95% CIs**. Sensitivity check: a cluster bootstrap by **fighter**, the attacker, because specialists recur (S8). No tuned ridge penalty.
- **Missing and "unclear" states (S7).** Report how often each factor is unclear, split by outcome. Primary analysis: complete cases plus an explicit `unclear` level. Sensitivity checks: unclear coded as each extreme. If unclear-rates differ a lot by outcome, say the factor can't be estimated from broadcast footage.
- **Blinding and reliability (S6).** Label factor states at the landmark **before watching the ending**: pause at start + L and code it, then play on and code the outcome. Get a **second rater** (a training partner) on ≥ 30 attempts for inter-rater κ. Self-relabeling only measures your own consistency.
- **Selection (S9).** Sampling by outcome alone leaves odds ratios consistent (only the intercept moves). But highlight packages and replays favor clear, finished chokes, so selection also depends on the factors. Mitigate with fight-based sampling (§3.2), `found_via` stratification, and labeling from the live feed, never replays.
- **Report:** odds ratios with CIs, a forest plot, and plain language ("under the chin vs not: 2.1× the odds, 95% CI 1.1–4.0"; illustrative numbers). Absolute finish probabilities come only from the fight-sampled subset.
- **Secondary:** a discrete-time hazard model. 1-s bins of the current factor states; finish vs escape as competing outcomes; bell = censored. It shows *when* factors matter.
- **Honesty rules:** associations, not causes; wide CIs are a result; exploratory findings are labeled exploratory; no hunting through 20 factors.

### 5b. Live predictor (for the overlay)
**Refit the same model family on auto-detected factor states (S11)**, not on the human-label coefficients. Measurement error in detected states otherwise pulls probabilities toward the base rate and mis-ranks the factors shown. The overlay's factor arrows come from the refit model. The write-up states how well detection agrees with human labels, per factor (κ). A LightGBM model is only allowed if it beats this one clearly on the harness, and it's explained with SHAP values (per-factor contributions to one prediction).

**Features, and how to compute them from pose**
- Snapshot features at *t*: (no time-held or end-time features); hooks / body-triangle proxy (attacker ankles near the defender's hips); arm depth (attacker wrist past the defender's far shoulder); two-on-one defense (both defender wrists on the choking arm); defender's head and hips turning toward the attacker (escape direction); round time remaining; distance to the cage edge, if detectable.
- **Fighter priors** from ufcstats (no video): defender's submission defense and attacker's submissions per 15 minutes, **computed only from fights *before* this fight's date**. Career totals include this fight and later ones, which leaks the label (critique #8). These could be a large share of the signal, so they're also a baseline.
- Model: logistic regression, then LightGBM. Calibrate with isotonic regression inside cross-validation.
- Upgrade (optional): a discrete-time **hazard model**, which predicts "tap in the next second" vs "escape in the next second" (competing risks) and turns that into an overall P(finish).

**Leak-free evaluation protocol (the important part)**
- Make predictions at fixed horizons *t* ∈ {1, 2, 3, 5, 8} s after `start_s`.
- At each *t*, include only attempts still ongoing **and whose outcome is at least 2 s away**. Report how many attempts that leaves at each *t*.
- Metrics: ROC-AUC, PR-AUC (finish = positive), Brier score, reliability plot. Bootstrap 95% confidence intervals over fights.
- Baselines the CV model **must beat**: (B0) base rate; (B1) **non-video attempt context**: round, round time left at the attempt start, fight time (elapsed time alone is constant within a horizon, so its AUC is 0.5 by construction, critique #7; the harness rejects it); (B2) B1 + as-of-date fighter priors. **If it can't beat B2, say so in the write-up. That's still an honest result.**
- **Measure B2 first, before any labeling** (critique experiment 3): with stats data alone, predict "the round ended by RNC | a submission attempt was scored", using as-of priors vs full-career priors. The gap shows the size of the leak, and the as-of AUC is the bar to clear.
- Also report 5b metrics with t measured from the **detected** start (Phase 4), not just your labeled start, because the demo runs on detections (critique #20).

| | |
|---|---|
| Realistic target (est.) | ROC-AUC 0.65–0.75 at t = 3 s. With about 30 test attempts (about 12 finishes), the **95% CI is about ±0.2** (Hanley–McNeil, critique #11), so the locked test set alone can't tell 0.65 from 0.75. Use cross-validation over all fights for the main numbers and treat the locked test set as a sanity check. |
| Risks | Small sample, so confidence intervals overlap the baseline. Pose loss right when it matters, because the choke is the most occluded moment. A lot of the outcome depends on things you can't see, like grip strength and fatigue. |
| Extra eval for 5b | How well the auto-detected factor states agree with your labels (κ per factor). An overlay explanation is only as good as that agreement. |
| Time (est.) | 15–25 h (science write-up included) |
| **Go/no-go** | Science: there's a pre-registered analysis with CIs, whatever the result. Predictor: beats B2 on mean AUC across horizons in cross-validation (harness: `compare_to_baseline`). If it doesn't, ship the overlay with B2 + elapsed time and say so. |

---

## Phase 6 — Video overlay

**Goal:** A recorded clip that shows "RNC ATTEMPT", a finish-probability bar, a small line chart of the probability over time, and the **top 2–3 factors driving it right now**, e.g. "▲ under chin, ▲ body triangle, ▼ two-on-one". These come from the 5b model's per-factor contributions. The renderer lives in `tools/overlay/` (main session). Its timeline input needs one extra column, `factors`: a JSON list of (name, signed contribution).

**Simplest approach:** Run offline on Kaggle: pose → detection → probability → draw with OpenCV → encode with ffmpeg. Smooth the probability with an exponential moving average. Show it only while detection confidence is above the threshold, and hide it during replays and cuts.

| | |
|---|---|
| Eval | Watch it next to the ground truth on 5 locked-test fights. Write down any confusing moments. |
| Risks | Flickering probability (fix with smoothing). Copyright if you publish UFC clips: overlays on UFC frames stay private (interviews). Public versions are skeleton-only renders on a blank background (FOOTAGE.md). |
| Time (est.) | 6–10 h |
| **Go/no-go** | Someone who doesn't train BJJ can follow the overlay without you explaining it |

---

## Phase 7 — Expansion

**Goal:** More submission types, tested on fights the model never saw.

- Next types by frequency: guillotine, arm-triangle, d'arce, triangle, armbar, kimura. Each needs about 80–150 attempts (est.).
- Reuse the Phase 3 tooling. The schema only gains a `sub_type` column.
- Tests: (a) a **temporal split**: train on events up to 2023, test on 2024 and later; (b) unseen weight classes; (c) different broadcast eras and camera styles within the UFC (e.g. pre-2016 vs now).
- Expect a metric drop on each shift, and report it.

| | |
|---|---|
| Time (est.) | 25–40 h per new submission type, mostly labeling |
| **Go/no-go** | Only start after Phases 4–6 work end-to-end for RNC |

---

## 8. Critical path

```
Labeler + PREREG ──► pilot (15) ──► labeling (≈150, hand-coded factors) ──► 5a science result   ← the core; needs NO pose
                          │
private clips ──► 2b pose ──► Phase 4 detector ──► 5b live model ──► Phase 6 overlay   ← the showcase; runs in parallel
stats data ──► leak-free B2 baseline (the bar 5b must clear)
```
**Your labeling hours drive the schedule.** GPU quota, model choice and code speed barely matter by comparison.

## 9. Schedule: weeks, not months (est.)

**What actually limits speed: your labeling hours.** Everything else runs in parallel or unattended:

| Work | Who | Hours (est.) |
|---|---|---|
| Labeling ~150 attempts | **you** | about 4 min in the labeler + 5–25 min to find the attempt (successes fast, failures slow) → **30–50 h** total. The 15-attempt pilot gives the real number. |
| Pose on private clips (laptop CPU, 1–3 fps) | machine, overnight | about 5–10 h unattended |
| Code (Phases 4–6, stats baseline, analysis) | build/main sessions | Runs in parallel while you label; not the bottleneck |

| At your pace of… | Labeling done in | Working demo + write-up |
|---|---|---|
| 10 h/week | about 4 weeks | about **5 weeks** |
| 20 h/week | about 2 weeks | about **3 weeks** |

### Parallel tracks, week by week (at about 15–20 h/week of labeling)

| Week | You | Build session | Main session |
|---|---|---|---|
| **1** | Footage set up (FOOTAGE.md ✅); clip and label the **15-attempt pilot** in `tools/labeler` (blind factor coding at +2 s); ask a training partner to double-label ~30 | Phase 2 fixes (swap augmentation); **leak-free B2 stats baseline** (no video); CPU pose smoke test on the pilot clips (2b go/no-go) | Commit `PREREG.md` **before** the pilot outcomes are coded; review the pilot timing → final labeling budget |
| **2** | Label to about 70–80 attempts (fight-sampled, `found_via` recorded) | Pose on all clips overnight; Phase 4 v0 detector on labeled clips; harness wired to `labels.csv` | Rules tweaks from the pilot (no code changes after PREREG); κ check on the first double-labeled batch |
| **3** | Label to about 150; partner finishes double-labeling | Phase 4 final; Phase 5b refit on detected states; overlay renders (private) + skeleton-only public renders | **Freeze labels → run 5a** (Firth ORs, forest plot, hazard check) |
| **4** (buffer) | Review failure cases; record the interview demo | Polish; locked-test run (single shot) | Write-up: "What finishes the RNC in the UFC: N attempts" |

**Rules for going fast without cheating:**
- PREREG is committed before outcomes are seen.
- The test-set hash rule is frozen at the start of week 1.
- The 5a analysis runs **once**, on frozen labels.
- The locked test set is run once, at the end.

**Go/no-go points stay the same:** 2b pose (end of week 1), the pilot cost and κ (end of week 1), Phase 4 F1 (week 3).

## 10. Top risks

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | Pose collapses on tangled broadcast ground footage | Medium–high | Week-2 smoke test; fine-tune on corrected frames; appearance-feature fallback |
| 2 | Not enough labeled attempts (especially failures) | High | Stats-driven candidates + pre-labeler; minimum viable 100; RNC only |
| 3 | Success prediction doesn't beat the stats-only baseline | Medium | Report it honestly; that's still a strong evaluation story |
| 4 | Copyright and license on UFC footage and the NC data | Certain (for public/commercial use) | Keep video private; publish derived data and skeleton-only renders (FOOTAGE.md) |
| 5 | Leakage making results look better than they are | Medium | Fight-level splits, a locked test set, the leak-free horizon protocol |
