# RNCV code tour

For the owner: you know BJJ and Python, you're new to ML and computer vision. Read top to bottom, or jump to the stop you want.
Legend: 🟢 works today · 🟡 partial · ⚪ planned. All commands run from the repo root. Three short-path venvs exist (Windows long-path DLL issue, see CLAUDE.md): `rncv` (pose + training), `ufc-cv` (OpenCV overlay), `ufc-eval` (eval harness tests).

```
PY_RNCV=C:/Users/netan/.venvs/rncv/Scripts/python
PY_CV=C:/Users/netan/.venvs/ufc-cv/Scripts/python
PY_EVAL=C:/Users/netan/.venvs/ufc-eval/Scripts/python.exe
```

---

## 1. Map

```
 MAIN TRACK (the live overlay)
 ─────────────────────────────
 UFC clip (data/clips/*.mp4, local only)
   │  🟢 src/pose_smoke.py        RTMO-m pose model, CPU: every person → 17 keypoints
   ▼
 raw people (many: fighters + referee + crowd + duplicates)
   │  🟢 src/two_fighters.py      pick 2 fighters, track them, fill gaps ≤ 0.5 s
   ▼
 data/pose/<clip>.npz             kpts [frames, 2 fighters, 17, (x,y,conf)]
   │  🟢 src/features.py          keypoints → numbers a model can use (178 or 350)
   ▼
 position classifier              🟢 src/train_baseline.py (GBM, trained on VICOS gym footage)
   │                              🟢 src/back_rule.py (no-training "is this back control?" rule)
   ▼
 attempt detector                 ⚪ "a choke has started, here is when"
   ▼
 finish-probability model         ⚪ P(finish | what we see so far), at 1/2/3/5/8 s horizons
   ▼
 preds.csv  (t_s, sub_type, prob, factors)
   │  🟢 tools/overlay/overlay.py   (works now on fake predictions)
   ▼
 clip with probability bar + sparkline + top factors

 SIDE TRACK (the science + the training labels)
 ──────────────────────────────────────────────
 UFC stats CSVs (phase3_labels/raw_sources, from ufcstats.com)
   │  🟢 build_candidates.py → build_fighter_priors.py → build_queues.py
   ▼
 labeling queues (successes, failures, random_10)
   │  🟡 tools/labeler/index.html   you watch a clip, press keys, code the 12 landmarks
   ▼
 phase3_labels/labels.csv          ⚪ does not exist yet (your pilot creates it)
   │  🟢 tools/eval_harness/       scoring rules, already written + tested
   ▼
 ⚪ science analysis (research/rnc_science/PREREG.md: frozen plan, FACTORS.md: code book)
 ⚪ also feeds labels back into the main track as training data for the attempt/finish models
```

---

## 2. Stop by stop

### Stop 1 · The question and the rules (no code, 10 min)
- [`CLAUDE.md`](../CLAUDE.md), [`PROGRESS.md`](../PROGRESS.md), [`research/rnc_science/PREREG.md`](../research/rnc_science/PREREG.md) (frozen pre-registration: what we will test, before looking at results) and [`FACTORS.md`](../research/rnc_science/FACTORS.md) (the code book: every BJJ detail we label, e.g. forearm placement).
- Why it matters: every later file exists to serve these. Nothing here is run.

### Stop 2 · `src/vicos_data.py` 🟢: the training data and how not to cheat
- **What:** loads VICOS, a public dataset of BJJ sparring frames, each with two athletes' skeletons and a position label (18 classes, e.g. `mount1` = athlete 1 on top in mount). Builds the train/test splits.
- **Look at:** [`load()`](../src/vicos_data.py:35), [`time_block_folds()`](../src/vicos_data.py:54). The 16 videos are really 6 sparring sessions seen by up to 3 cameras, so a random split would put the *same moment* in train and test. Instead it holds out contiguous time blocks and drops frames within 300 frames (~10 s) of the test block.
- **In/out:** `data/raw/vicos/annotations.json` → table of frames + folds.
- **Try it (seconds):** `$PY_RNCV -I src/vicos_data.py` prints dataset stats.

### Stop 3 · `src/features.py` 🟢: from skeletons to numbers
- **What:** a model can't read "two stick figures", so this turns 2×17 keypoints into a flat list of numbers: positions (centred and scaled so camera zoom doesn't matter), joint angles, torso direction, distances between the athletes. Missing joints become NaN.
- **Look at:** [`build()`](../src/features.py:30) (178 features, athlete order matters) and [`build_role_invariant()`](../src/features.py:80) (350 features, "top athlete" always first, so swapping who is who changes nothing).
- **In/out:** poses `[N, 2, 17, 3]` → feature matrix `[N, 178 or 350]`.
- **Try it:** `$PY_RNCV -I -c "import sys; sys.path.insert(0,'src'); import numpy as np, features; p=np.random.rand(4,2,17,3); print(features.build(p).shape, features.build_role_invariant(p).shape)"`

### Stop 4 · `src/train_baseline.py` 🟢: the position classifier
- **What:** trains a gradient-boosting model (many small decision trees voting) or a small neural net (`--model mlp`) to name the position, scored on the 5 time-block folds. `--swap-aug` trains on every frame twice (as-is and with the two athletes swapped) because UFC tracker IDs are arbitrary.
- **Look at:** [`make_model()`](../src/train_baseline.py:41), [`swap_label_index()`](../src/train_baseline.py:62) (maps `mount1`↔`mount2`), [`main()`](../src/train_baseline.py:76) for the fold loop. Results: macro-F1 0.63 (swap-aug GBM), see `reports/TRAINING_STATUS.md`. Weak classes: half guard, takedowns.
- **In/out:** VICOS annotations → `reports/metrics_*.json`, `per_class_*.csv`, `oof_*.csv`, `confusion_*.png`.
- **Caveat:** same gym, same athletes in train and test. It shows the features separate positions, **not** that it works on UFC footage.
- **Try it (about a minute, estimate):** `$PY_RNCV -I src/train_baseline.py --model gbm --train-stride 8 --tag _tour` (coarser training stride for speed; writes `*_tour` files into `reports/`, safe to delete).

### Stop 5 · `src/back_rule.py` 🟢: back control without machine learning
- **What:** a hand-written BJJ rule on two skeletons: both facing the same way, close, attacker's chest on defender's back, head by defender's neck. Thresholds are grid-searched on training folds only. Recall 0.78–0.83, precision 0.85 on VICOS.
- **Look at:** [`pair_geometry()`](../src/back_rule.py:45) (the four measurements), [`apply_rule()`](../src/back_rule.py:69), [`fit_thresholds()`](../src/back_rule.py:78).
- **In/out:** VICOS poses → `reports/back_rule.md/.json`.
- **Try it:** `$PY_RNCV -I src/back_rule.py`

### Stop 6 · `src/pose_smoke.py` 🟢: video to skeletons (the CV heart)
- **What:** runs RTMO-m (a pose model: finds every person and their 17 joints in one pass) on each frame. The key discovery in `research/pose_sweep/FINDINGS.md`: the default confidence cutoff 0.7 throws away the tangled second fighter, so we use 0.3 and clean up afterwards.
- **Look at:** [`run_clip()`](../src/pose_smoke.py:62) (decode → RTMO → select → track → save), [`draw()`](../src/pose_smoke.py:43) (preview colours), CLI flags at [line 160](../src/pose_smoke.py:160).
- **In/out:** `data/clips/*.mp4` → `data/pose/<clip>.npz` + `<clip>_preview.mp4` + `reports/pose_smoke.md`.
- **Try it (under a minute; first run may download the model):** `$PY_RNCV -I src/pose_smoke.py --clips data/clips/gsp_bisping.mp4 --max-frames 20 --no-preview`. Then open an existing `data/pose/*_preview.mp4`.

### Stop 7 · `src/two_fighters.py` 🟢/🟡: which two skeletons are the fighters?
- **What:** after RTMO there may be 5 skeletons (fighters, referee, crowd, duplicates). Steps: drop small boxes (crowd), drop duplicates of the same body, with 3+ left keep the most-overlapping pair (referee guess), then a 2-slot tracker (Hungarian matching on joint positions) keeps each fighter's identity and fills a vanished fighter from their last pose for ≤ 0.5 s, flagged "filled".
- **Look at:** [`select()`](../src/two_fighters.py:52), [`TwoSlotTracker.update()`](../src/two_fighters.py:85), [`upper_ok()`](../src/two_fighters.py:118).
- 🟡 **Known weakness:** the referee rule is not solved. On the sample clips it sometimes keeps the referee and drops a sprawled fighter, so tracked-fighter coverage (64–97%) is an upper bound. Candidate fix: a fighters-only detector, not built.
- **Try it:** read the saved evidence in `research/pose_sweep/FINDINGS.md`, and look at the red/green frames in `data/pose/select2/`.

### Stop 8 · `research/pose_sweep/` 🟢: how we learned the threshold was the culprit
- **What:** `sweep.py` runs RTMO on a grid of thresholds and counts how often 2+ people are found; `select2.py` is the prototype of Stop 7 (also tried and rejected a black-shirt referee rule). `FINDINGS.md` is the write-up, `results.json` the numbers.
- **Look at:** [`sweep.py main()`](../research/pose_sweep/sweep.py:39), [`select2.py select()`](../research/pose_sweep/select2.py:103).
- **Try it:** read `FINDINGS.md` section 1's table. (Re-running `sweep.py` takes minutes, skip.)

### Stop 9 · `tools/eval_harness/` 🟢: the scoring rules, as code
- **What:** the anti-cheating rules from the plan, written so a model can't break them by accident. `splits.py`: a fight is in the test set iff a salted hash of its id is below 0.2, fixed forever; same-fighter leakage is purged. `horizons.py`: scores finish probability at 1/2/3/5/8 s after attempt start; `bell` (time ran out) is censored, not a failure; bootstrap over fights; refuses leaky columns and degenerate baselines. `events.py`: turns probabilities into attempt segments and scores them.
- **Look at:** [`lock_test_groups`/`group_cv`](../tools/eval_harness/splits.py:50), [`horizon_frame()`](../tools/eval_harness/horizons.py:82), [`horizon_metrics()`](../tools/eval_harness/horizons.py:125), [`compare_to_baseline()`](../tools/eval_harness/horizons.py:150), [`segments_from_probs()`](../tools/eval_harness/events.py:12), [`event_metrics()`](../tools/eval_harness/events.py:80).
- **In/out:** a `labels.csv` plus model predictions → AUC, Brier, CIs, event F1. Nothing real feeds it yet (no labels).
- **Try it (~20 s):** `$PY_EVAL -m pytest -q -p no:cacheprovider tools/eval_harness` (11 tests).

### Stop 10 · `phase3_labels/` 🟢: where the attempts to label come from
- **What:** turns ufcstats CSVs into lists of fights to watch. `build_candidates.py`: 683 RNC finishes + 3,436 fighter-rounds with submission attempts but no submission finish. `build_fighter_priors.py`: each fighter's record **as of the day before the fight** (no peeking at their own outcome; `test_priors_leak.py` checks it). `build_queues.py`: the hybrid sampling from PREREG (successes, failures with ≤ 3 per fighter, plus a seeded `random_10`). `draw_pilot.py` and `pilot_15_RETIRED.csv` are retired.
- **Look at:** [`build_candidates.main()`](../phase3_labels/build_candidates.py:81), [`compute_priors()`](../phase3_labels/build_fighter_priors.py:66), [`take()`](../phase3_labels/build_queues.py:62). Schema: `LABEL_SCHEMA.md`; first session plan: `PILOT.md`.
- **Try it:** `$PY_RNCV -I phase3_labels/test_priors_leak.py` (if pandas missing in that venv, use `$PY_EVAL`), then open `phase3_labels/labeling_queue_successes.csv`.

### Stop 11 · `tools/labeler/index.html` 🟡: you, labeling
- **What:** one offline HTML page (no server, video never uploaded). Load the queue CSVs and a local clip, sync the round clock, press S at the start of the choke; the video plays 2 s and **freezes** so you code the 12 landmarks blind to the ending; then mark the end and the outcome. Writes `labels.csv` rows in LABEL_SCHEMA format.
- **Look at:** [`startAttempt()`](../tools/labeler/index.html:375), [`blindLock()`](../tools/labeler/index.html:238), [`saveAttempt()`](../tools/labeler/index.html:405), [`toCSV()`](../tools/labeler/index.html:206).
- 🟡 Tested only on synthetic clips; the 4-minute-per-attempt target is untimed until your pilot.
- **Try it:** double-click the file in Chrome/Edge, load the three queue CSVs, and read the on-screen key legend. Details: `tools/labeler/README.md`.

### Stop 12 · `tools/overlay/` 🟢 (on fake data): the visible end product
- **What:** draws submission type, probability bar (red→green), 8 s sparkline and top-2 factors on a clip. It only uses the latest prediction at or before each frame, so it can't peek at the future. Predictions come from a CSV, so the real model plugs in later with no renderer changes.
- **Look at:** [`render()`](../tools/overlay/overlay.py:73), [`draw_panel()`](../tools/overlay/overlay.py:44), [`pred_at()`](../tools/overlay/overlay.py:38). Input format: `t_s, sub_type, prob, factors`.
- **Try it (seconds):** `cd tools/overlay` then `$PY_CV make_demo.py` and `$PY_CV overlay.py --video demo_clip.mp4 --preds demo_preds.csv --out demo_overlay.mp4`; open the mp4.

### Stop 13 · `notebooks/kaggle_yolo_pose_vicos.ipynb` 🟡
- **What:** Kaggle GPU notebook that re-extracts VICOS keypoints with YOLO11-pose, same JSON format, to compare pose models. VICOS only; **never UFC footage on Kaggle**. Not run yet as far as the README says; steps are in `README.md`.
- **Try it:** just skim the markdown cells.

---

## 3. Glossary

- **Keypoint:** one body joint (nose, shoulder, elbow, wrist, hip, knee, ankle...) as an (x, y) pixel position. COCO-17 = 17 per person.
- **Confidence score:** the model's own 0–1 belief that a detection or joint is right. Not a probability you can trust blindly; it drops when fighters are tangled.
- **NMS (non-maximum suppression):** deletes a detection if its box overlaps a better one too much. Good for crowds, bad for grapplers, since the second fighter overlaps the first.
- **Macro-F1:** F1 (balance of precision and recall) computed per class, then averaged equally, so rare positions count as much as common ones.
- **Time-block fold:** one test chunk is a contiguous stretch of every session, with a buffer removed from training around it, so near-identical neighbour frames can't leak.
- **Swap augmentation:** training on each frame twice, with the two athletes' order and labels swapped, so the model can't key on "who is athlete 1".
- **Role-invariant:** features that don't change when the two athletes are swapped, e.g. top athlete always first.
- **Landmark:** a pre-registered observable detail at the moment the choke starts (e.g. forearm placement), coded blind before seeing the outcome.
- **Censoring:** the outcome is unknown, not a failure: the bell ended the round with the choke still on, so that attempt is dropped from scoring, not counted as "escaped".
- **κ (kappa):** agreement between two labelers beyond chance. 0 = chance, 1 = perfect; used to check that labels are reproducible.

---

## 4. What's real vs. planned

| Piece | Status | Notes |
|---|---|---|
| RTMO pose on laptop CPU | 🟢 | Works on 3 local UFC clips. Needs score 0.3 / nms 0.65 |
| Two-fighter selection + tracking | 🟡 | Coverage 64–97% on 3 clips; referee sometimes kept instead of a fighter |
| Position classifier (VICOS) | 🟢 | Macro-F1 0.63; weak on half guard, takedowns. Not yet tested on UFC footage |
| Back-control rule | 🟢 | Recall 0.78–0.83, precision 0.85 on VICOS. UFC comparison still to do |
| Attempt detector | ⚪ | No code; `events.py` can score it once it exists |
| Finish-probability model | ⚪ | No code; `horizons.py` is ready to score it |
| Eval harness | 🟢 | 11 tests pass; nothing real has been scored yet |
| Candidate lists, priors, queues | 🟢 | CSVs built; leak test exists |
| Labeler | 🟡 | Built and synthetic-tested; untimed on real clips |
| `labels.csv` | ⚪ | Not created; your pilot labeling makes it |
| Science analysis | ⚪ | PREREG frozen (v1.0, b8d817d); no analysis code until labels exist |
| Overlay | 🟡 | Renderer works; only fake predictions |
| Kaggle YOLO notebook | 🟡 | Written, not run |

Housekeeping: `src/pose_smoke.py.tmp.*` in `src/` looks like a leftover from an interrupted save; it isn't code to read.

---

## 5. Suggested 30-minute self-tour

1. **(5 min)** Read `PROGRESS.md` and skim PREREG's headings. Know the question before the code.
2. **(5 min)** Watch `data/pose/gsp_bisping_preview.mp4` and one other. Spot the thin "filled" skeletons and any frame where the referee is kept. This is the main weak point (Stop 7).
3. **(8 min)** Read `research/pose_sweep/FINDINGS.md` section 1, then [`select()`](../src/two_fighters.py:52). Run the Stop 6 command with `--max-frames 20`.
4. **(7 min)** Run Stop 5 (`back_rule.py`) and read `reports/back_rule.md`, then open `reports/confusion_gbm_swapaug.png`. Which positions get confused?
5. **(5 min)** Run the overlay demo (Stop 12) and open `tools/labeler/index.html` in Chrome. See the end product, and the tool you'll use for the pilot.

**Your next action:** the pilot labeling, which unlocks everything marked ⚪.
