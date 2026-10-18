# UFC Submission CV — Project Plan

> Owner: you. Code, environment and `data/` belong to the build session (`build-phase2`). This document is the plan.
> Every time, accuracy and compute figure here is an **estimate**, unless a source is linked.

## Chosen direction (2026-10-18)

**Core: "Science-based RNC."** Which details of a rear-naked choke predict a finish? Arm under the chin vs on the jaw, hooks vs body triangle, flattening the defender, the defender's hand fighting, round, and time held. Each effect is reported with a confidence interval.
**Showcase: the live overlay.** It shows the finish probability *plus the factors driving it* right now.

What this changes in the plan:
- **Phase 3:** the labels must record each factor *over time* (§3.4b). These are the science variables, so labeling them carefully matters more than the attempt count alone.
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
| Pose (main) | [rtmlib](https://github.com/Tau-J/rtmlib) with **RTMO-m** (one-stage, built for crowded scenes) or RTMPose + detector | Apache-2.0 | ONNX runs on a CPU for small tests and on a Kaggle GPU for bulk work. Clean license if you ever charge money. |
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

### 3.1 Footage and copyright (not legal advice)
- UFC footage is copyrighted. YouTube's and Fight Pass's terms forbid downloading. There's **no clean $0 path** to downloadable UFC video. Pick knowingly:
  - Watch through legitimate access (UFC YouTube free fights, Fight Pass) and keep any local copies **private and never redistributed**.
  - Store only **derived data** in the project: keypoints, timestamps and labels. Keep raw video out of git and out of Kaggle public datasets. Kaggle notebooks with private datasets are fine.
  - For anything public (demo reel, social posts), prefer gym footage you recorded, with every athlete's consent.

### 3.2 Finding candidates from stats
1. Scrape ufcstats.com fight pages and get: `method`, `round`, `time`, and per-round `sub_att` and `ctrl` (control time) for each fighter.
2. **Successes:** `method` contains "Rear Naked Choke" → the exact round and clock time of the finish. Find the attempt start by scrubbing backward about 60 s.
3. **Failure candidates:** rounds with `sub_att ≥ 1` and high control time, in fights that did *not* end by RNC in that round. You scrub those rounds by hand, so failures cost more labeling time. Note that a `sub_att` count can be any submission type.
4. **Prior:** an older Fightnomics analysis says RNC attempts finish about [41% of the time](https://www.lowkickmma.com/cagepotato-databomb-2-breaking-down-submission-success-rates-in-ufc-fights/) (denominator not verified). RNC accounts for [about 49% of UFC choke finishes](https://combatsportslaw.com/2020/12/26/physician-reviews-and-analyzes-all-choke-submissions-in-ufc-history/) (through 2020). Expect classes to be roughly 40/60, success vs failure.

### 3.3 AI pre-labeling (saves your hours)
Run pose → tracker → Phase 2 position model over every candidate round. Output **back-control segments** longer than 3 s as a review list, each with a start time. You review only those segments, plus a 10 s buffer, instead of whole 5-minute rounds. Target: under 4 minutes of review per round (est.).

### 3.4 Label schema (`labels/rnc_attempts.csv`)

| Column | Type | Rule |
|---|---|---|
| `attempt_id` | str | `{fight_id}_r{round}_{n}` |
| `fight_id` | str | ufcstats fight ID. **This is the split key.** |
| `event_date` | date | For temporal splits in Phase 7 |
| `clip_file` | str | Local path (never shared) |
| `round` | int | |
| `start_s` / `end_s` | float | Seconds in the clip file. Start and end rules below. |
| `round_clock_start` | mm:ss | Round clock when the attempt starts, if visible |
| `attacker_corner` | red/blue | |
| `attacker_track_side` | left/right/unknown | Fighter position on screen at `start_s`, to start tracking |
| `outcome` | enum | `SUCCESS_TAP`, `SUCCESS_REF`, `SUCCESS_UNCONSCIOUS`, `FAIL_ESCAPE`, `FAIL_POSITION_CHANGE`, `FAIL_BELL` |
| `hooks` | enum | `both_hooks`, `body_triangle`, `one_hook`, `none`, at start |
| `choke_arm_depth` | enum | `under_chin`, `on_jaw`, `unclear` (your best judgement at the deepest point) |
| `visible_frac` | 0–1 | Rough share of the attempt shown live (no cuts or replays) |
| `has_replay` | bool | A replay of this attempt exists in the clip. Mark its time range in `notes`. |
| `labeler_conf` | 1–3 | How sure you are |
| `notes` | str | |

**Start rule:** the first frame where the attacker's forearm crosses the front of the defender's neck *or* jaw, from behind, with clear intent to choke. Hand-fighting before the arm crosses doesn't count.
**End rule:** the first frame of one of these:
- `SUCCESS_TAP`: a visible tap (hand or foot) or a verbal tap the referee acts on. `end_s` = tap frame.
- `SUCCESS_REF`: the referee stops the fight without a tap. `end_s` = referee contact.
- `SUCCESS_UNCONSCIOUS`: the defender goes limp before a tap or stoppage. `end_s` = first limp frame.
- `FAIL_ESCAPE`: the defender clears the choking arm off the neck for > 2 s, *or* turns to face the attacker.
- `FAIL_POSITION_CHANGE`: the attacker abandons the choke for another submission, strikes or a new position for > 2 s.
- `FAIL_BELL`: the round ends during the attempt.
- **Re-attacks:** if the arm comes back after a `FAIL` end, that's a new `attempt_id`.
- **Exclude** (keep in the file, `outcome` = `EXCLUDE`): `visible_frac` < 0.5, or the attempt is only shown in replay.

### 3.4b Factor timeline (`labels/rnc_factors.csv`) — the science variables

The per-attempt columns above (`hooks`, `choke_arm_depth`) give one value per attempt. Effects that change *while* the attempt unfolds need a timeline. Log one row whenever a factor changes state (usually 3–8 rows per attempt):

| Column | Values | Rule |
|---|---|---|
| `attempt_id`, `t_s` | | Seconds since `start_s` when the new state begins |
| `arm` | `under_chin`, `on_jaw`, `over_face`, `off` | Where the choking forearm sits |
| `grip` | `rnc_figure4`, `palm_to_palm`, `hand_on_shoulder`, `none` | How the choke is locked |
| `lower_body` | `both_hooks`, `body_triangle`, `one_hook`, `none` | |
| `flattened` | yes/no | Defender is chest-down, with hips pinned flat |
| `defender_hands` | `two_on_one`, `one_hand`, `none` | Hand fighting on the choking arm |
| `defender_turning` | yes/no | Shoulders or hips turning toward the attacker (escape) |

- These columns *are* the variables of the science study. Keep the codes stable; any change goes through `research/rnc_science/`.
- **Pre-label later:** once Phase 4 exists, pose geometry can propose `arm`/`lower_body`/`defender_hands` states and you only correct them.
- **Non-visual covariates**, joined from ufcstats by `fight_id`: round, round time left, the defender's career submission defense, the attacker's submission rate, and weight class.
- **Agreement:** κ is checked for every factor, not just the outcome. Any factor below κ 0.6 is reported as unreliable, not interpreted.

**Quality check:** two weeks after labeling the first 20 attempts, re-label them blind. Target Cohen's κ (chance-corrected agreement) ≥ 0.8 on outcome, and start-time differences under 1 s. If you miss that, tighten the rules before going further.

### 3.5 Targets

| | Count (est.) |
|---|---|
| Minimum viable | 100 attempts (≈40 success / 60 fail), ≥ 70 fights |
| Target v1 | **150 attempts, ≥ 100 fights** |
| Locked test set | 20% of fights. Chosen once, by `fight_id`, before any modeling, and never tuned on. |
| Negatives for Phase 4 | Back-control segments with no attempt, which come free from pre-labeling |
| Labeling time | About 15–20 min per attempt including search and the factor timeline, so **35–50 h** total |

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
| Eval | `GroupKFold` by `fight_id` on the training fights, then a single run on the locked test set. Metrics: event-level F1 at tIoU ≥ 0.3, PR-AUC per window, **false alarms per fight-hour**, and median start-time error. |
| Baselines | "Back control longer than 3 s = attempt" rule, using Phase 2 output only |
| Risks | Occlusion hides the choking arm. Negatives are rare and close to the positives (hand-fighting on the back looks like an attempt). Replays count as duplicates (detect them, or drop them using `has_replay` ranges). |
| Time (est.) | 12–18 h |
| **Go/no-go** | Event F1 ≥ 0.5 and fewer than 3 false alarms per fight-hour on the locked test set (est. targets). Below that, use Phase 4 as a pre-labeler only and run Phase 5 on your hand-labeled segments. That still makes a valid demo. |

---

## Phase 5 — RNC science + live finish probability

**Goal 1 (core, science):** Estimate how much each RNC detail changes the chance of a finish, with confidence intervals.
**Goal 2 (showcase):** At each moment *t* seconds into an attempt, output P(finish) using only frames up to *t*, plus the factors pushing it up or down.

### 5a. Interpretable factor model (primary analysis)
- **Pre-register before looking at outcomes.** Write the factor list, codings and model in `research/rnc_science/` before fitting anything. With about 150 attempts and about 60 finishes, the data can support **about 5–6 predictors** (the common rule of thumb is about 10 events per variable). Pick them:
  - `arm` (under_chin vs other)
  - `lower_body` (body_triangle / both_hooks / less)
  - `flattened`
  - `defender_hands` (two_on_one vs not)
  - `round`
  - `log(time held)`
  - Everything else is exploratory and labeled as such.
- **Model:** **penalized logistic regression** (logistic regression with a small shrinkage penalty, ridge or Firth, which keeps estimates stable on small data). Use the factor states in the first 3 s, or at the deepest point; pick one in the pre-registration and keep it fixed.
- **Report:** **odds ratios** (how many times higher the odds of a finish are when the factor is present) with 95% CIs bootstrapped **by fight**, plus a forest plot. Translate to plain language, e.g. "under the chin vs on the jaw: 2.1× the odds (95% CI 1.1–4.0)". The numbers are illustrative.
- **Secondary analysis:** a discrete-time **hazard model**. Split each attempt into 1-s bins with the current factor states; outcome = finish within this bin; escape is a competing outcome. It shows *when* factors matter. Also check confounding, e.g. whether "under the chin" only looks strong because it comes later in an attempt.
- **Honesty rules:**
  - These are associations, not causes.
  - Wide CIs are a result, not a failure.
  - Don't test 20 factors and report the 2 that came out "significant".
  - Selection bias: attempts were found through stats and the pre-labeler, so ones the cameras missed are absent.

### 5b. Live predictor (for the overlay)
Use the same logistic family, fed by **auto-detected** factor states (pose geometry), so the overlay's explanations match the science model. A LightGBM model is only allowed if it beats this one by a clear margin on the harness, and even then it's explained with SHAP values, which split one prediction into per-factor contributions.

**Features, and how to compute them from pose**
- Snapshot features at *t*: elapsed time; hooks / body-triangle proxy (attacker ankles near the defender's hips); arm depth (attacker wrist past the defender's far shoulder); two-on-one defense (both defender wrists on the choking arm); defender's head and hips turning toward the attacker (escape direction); round time remaining; distance to the cage edge, if detectable.
- **Fighter priors** from ufcstats (no video): defender's career submission defense, attacker's submissions per 15 minutes. These could be a large share of the signal, so they're also a baseline.
- Model: logistic regression, then LightGBM. Calibrate with isotonic regression inside cross-validation.
- Upgrade (optional): a discrete-time **hazard model**, which predicts "tap in the next second" vs "escape in the next second" (competing risks) and turns that into an overall P(finish).

**Leak-free evaluation protocol (the important part)**
- Make predictions at fixed horizons *t* ∈ {1, 2, 3, 5, 8} s after `start_s`.
- At each *t*, include only attempts still ongoing **and whose outcome is at least 2 s away**. Report how many attempts that leaves at each *t*.
- Metrics: ROC-AUC, PR-AUC (finish = positive), Brier score, reliability plot. Bootstrap 95% confidence intervals over fights.
- Baselines the CV model **must beat**: (B0) base rate; (B1) elapsed time only; (B2) fighter priors + round time, no video. **If it can't beat B2, say so in the write-up. That's still an honest result.**

| | |
|---|---|
| Realistic target (est.) | ROC-AUC 0.65–0.75 at t = 3 s. Expect a confidence interval of about ±0.1 with roughly 30 test attempts. |
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
| Risks | Flickering probability (fix with smoothing). Copyright if you publish UFC clips. Keep the public demo on your own gym footage, or only show UFC clips privately or briefly in interviews. |
| Time (est.) | 6–10 h |
| **Go/no-go** | Someone who doesn't train BJJ can follow the overlay without you explaining it |

---

## Phase 7 — Expansion

**Goal:** More submission types, tested on fights the model never saw.

- Next types by frequency: guillotine, arm-triangle, d'arce, triangle, armbar, kimura. Each needs about 80–150 attempts (est.).
- Reuse the Phase 3 tooling. The schema only gains a `sub_type` column.
- Tests: (a) a **temporal split**: train on events up to 2023, test on 2024 and later; (b) unseen weight classes; (c) a different camera style (another promotion, or gym footage).
- Expect a metric drop on each shift, and report it.

| | |
|---|---|
| Time (est.) | 25–40 h per new submission type, mostly labeling |
| **Go/no-go** | Only start after Phases 4–6 work end-to-end for RNC |

---

## 8. Critical path

```
Footage access ──► 2b pose smoke test ──► Phase 3 labeling (≥100) ──► Phase 4 ──► Phase 5 ──► Phase 6
        ▲                                   ▲
Phase 2 (VICOS) ────── "Back" pre-labeler ──┘   (Phase 2 speeds up Phase 3 but doesn't block it)
ufcstats scrape ───────── candidate list ───┘
```
**Your labeling hours drive the schedule.** GPU quota, model choice and code speed barely matter by comparison.

## 9. Weekly schedule (part-time, about 6–8 h/week, est.)

| Week | Milestone | Owner |
|---|---|---|
| 1 | Phase 2 CPU baseline on VICOS keypoints, with time-block-fold results | build session |
| 2 | **2b broadcast pose smoke test (go/no-go)**; ufcstats scrape → RNC candidate list | build + you |
| 3 | Phase 2 RTMO re-extraction; pre-labeler; label 15 pilot attempts; finalize the rules | you |
| 4 | **Pre-register the science analysis** (factors, codings, model) in `research/rnc_science/` before fitting any outcomes | you + main |
| 4–8 | Label to 100–150 attempts with factor timelines (about 8/week); κ check in week 5; lock the test fights in week 4 | you |
| 5–6 | Phase 4 v0 on the first 60 attempts (built while you keep labeling) | build |
| 8–9 | Phase 4 final on the locked test set | build + you review |
| 10–11 | Phase 5a science (odds ratios, forest plot, hazard check), then 5b live predictor vs baselines | build + you |
| 12 | Phase 6 overlay with factor explanations, plus the write-up: "What makes an RNC finish?" with CIs, and failure cases | both |
| 13+ | Phase 7: guillotine | you |

**Total to a working RNC demo: about 12 weeks part-time (est.).** If you can put in 15 h/week, it drops to about 6–7 weeks, but labeling still sets the pace.

## 10. Top risks

| # | Risk | Likelihood | Mitigation |
|---|---|---|---|
| 1 | Pose collapses on tangled broadcast ground footage | Medium–high | Week-2 smoke test; fine-tune on corrected frames; appearance-feature fallback |
| 2 | Not enough labeled attempts (especially failures) | High | Stats-driven candidates + pre-labeler; minimum viable 100; RNC only |
| 3 | Success prediction doesn't beat the stats-only baseline | Medium | Report it honestly; that's still a strong evaluation story |
| 4 | Copyright and license on UFC footage and the NC data | Certain (for public/commercial use) | Keep everything private and derived-only; public demo on your own footage |
| 5 | Leakage making results look better than they are | Medium | Fight-level splits, a locked test set, the leak-free horizon protocol |
