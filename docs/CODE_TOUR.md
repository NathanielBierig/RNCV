# RNCV code tour

For the owner: you know BJJ and Python, you're new to ML and computer vision. Read top to bottom, or jump to the stop you want.
Updated 2026-10-25. Legend: 🟢 works today · 🟡 partial · ⚪ planned. All commands run from the repo root. Three short-path venvs exist (Windows long-path DLL issue, see CLAUDE.md): `rncv` (pose + training), `ufc-cv` (OpenCV overlay), `ufc-eval` (eval harness tests).

Timings below are measured on this laptop. `$PY_*` are shorthand for these paths (type them out in PowerShell).

```
PY_RNCV=python
PY_CV=python
PY_EVAL=python
```

---

## 1. Map

```
 MAIN TRACK (the live overlay)
 ─────────────────────────────
 UFC clip (data/clips/*.mp4, local only)
   │  🟢 src/pose_smoke.py        RTMO-m pose model, CPU: every person → 17 keypoints
   │  🟡 src/yolo_pose_onnx.py    alternative: our fine-tuned YOLO-pose (models/rncv_pose_v1.onnx)
   ▼
 raw people (many: fighters + referee + crowd + duplicates)
   │  🟢 src/two_fighters.py      pick 2 fighters, track them, fill gaps ≤ 0.5 s
   │      └ src/referee.py        drop the referee by skin vs. black clothing
   ▼
 data/pose/<clip>.npz             kpts [frames, 2 fighters, 17, (x,y,conf)]
   │  🟢 src/features.py          keypoints → numbers a model can use (178 or 350)
   ▼
 position classifier              🟢 src/train_baseline.py (GBM, trained on VICOS gym footage)
   │                              🟢 src/back_rule.py (no-training "is this back control?" rule)
   ▼
 attempt detector                 🟡 research/attempt_clf: no-pose CLIP + logistic regression, ROC-AUC 0.70 (not usable yet)
   ▼
 finish-probability model         🟡 tools/mvp/demo.py: small stand-in fit on your labels (the real hazard model is ⚪)
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
   │  🟢 tools/labeler/index.html   you watch a clip, press keys, code the 12 landmarks
   ▼
 phase3_labels/labels.csv          🟡 36 attempts / ~20 fights so far (goal ~150 attempts)
   │  🟢 phase3_labels/qa_labels.py     read-only quality check → reports/labels_qa.md
   │  🟢 src/pose_attempts.py           does pose work INSIDE labeled attempts? → reports/pose_attempts.md
   │  🟢 tools/eval_harness/            scoring rules, already written + tested
   ▼
 ⚪ science analysis (research/rnc_science/PREREG.md: frozen plan, FACTORS.md: code book)
 ⚪ also feeds labels back into the main track as training data for the attempt/finish models
```

---

Big caveat since 2026-10-21: a fresh-eye review found the pose step **mixes the two fighters' skeletons** (see Stop 8c). So the attempt detector deliberately uses *no pose at all*, and the MVP demo takes attempt windows from your labels.

Also: `tools/preview/corner_preview.py` 🟢 draws red/blue-corner skeleton previews (a debugging view of the pose pipeline), and `notebooks/kaggle_finetune_pose/` 🟡 produces the fine-tuned pose model on Kaggle (public datasets only).

---

## 2. Stop by stop

### Stop 1 · The question and the rules (no code, 10 min)
- [`CLAUDE.md`](../CLAUDE.md), [`PROGRESS.md`](../PROGRESS.md), [`research/rnc_science/PREREG.md`](../research/rnc_science/PREREG.md) (frozen pre-registration: what we will test, before looking at results) and [`FACTORS.md`](../research/rnc_science/FACTORS.md) (the code book: every BJJ detail we label, e.g. forearm placement).
- Also now: [`docs/LABELING_GUIDE.md`](LABELING_GUIDE.md) (how to judge each of the 12 fields) and [`docs/rnc_codebook.html`](rnc_codebook.html) (picture code book, open in a browser).
- Why it matters: every later file exists to serve these. Nothing here is run.

### Stop 2 · `src/vicos_data.py` 🟢: the training data and how not to cheat
- **What:** loads VICOS, a public dataset of BJJ sparring frames, each with two athletes' skeletons and a position label (18 classes, e.g. `mount1` = athlete 1 on top in mount). Builds the train/test splits.
- **Look at:** [`load()`](../src/vicos_data.py:35), [`time_block_folds()`](../src/vicos_data.py:54). The 16 videos are really 6 sparring sessions seen by up to 3 cameras, so a random split would put the *same moment* in train and test. Instead it holds out contiguous time blocks and drops frames within 300 frames (~10 s) of the test block.
- **In/out:** `data/raw/vicos/annotations.json` → table of frames + folds.
- **Try it (about 50 s, verified; mostly loading the JSON):** `$PY_RNCV -I src/vicos_data.py` prints dataset stats.

### Stop 3 · `src/features.py` 🟢: from skeletons to numbers
- **What:** a model can't read "two stick figures", so this turns 2×17 keypoints into a flat list of numbers: positions (centred and scaled so camera zoom doesn't matter), joint angles, torso direction, distances between the athletes. Missing joints become NaN.
- **Look at:** [`build()`](../src/features.py:30) (178 features, athlete order matters) and [`build_role_invariant()`](../src/features.py:80) (350 features, "top athlete" always first, so swapping who is who changes nothing).
- **In/out:** poses `[N, 2, 17, 3]` → `(X [N, 178 or 350], feature names)` (role-invariant also returns a 3rd item).
- **Try it (3 s, verified):** `$PY_RNCV -I -c "import sys; sys.path.insert(0,'src'); import numpy as np, features; p=np.random.rand(4,2,17,3); print(features.build(p)[0].shape, features.build_role_invariant(p)[0].shape)"` → `(4, 178) (4, 350)`.

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
- ⚠ **Don't "try" this one casually:** every run **overwrites** `data/pose/<clip>.npz` and the table at the top of `reports/pose_smoke.md`, even with `--max-frames 5` (I clobbered both while verifying this tour). For a harmless look, open an existing `data/pose/*_preview.mp4` instead.

### Stop 7 · `src/two_fighters.py` + `src/referee.py` 🟢/🟡: which two skeletons are the fighters?
- **What:** after RTMO there may be 5 skeletons (fighters, referee, crowd, duplicates). `select()` drops small boxes (crowd), drops duplicates of the same body, then (new) drops the referee **by appearance**: `referee.py` measures the share of skin-coloured pixels on torso, upper arms and legs. Fighters are shirtless; the referee is in black. Skin is detected by chroma (YCrCb), not brightness, so dark-skinned fighters still read as skin while black fabric is neutral grey. That's why it doesn't repeat the failed "dark shirt" rule. With 3+ people left it still falls back to "keep the most-overlapping pair". A 2-slot tracker (Hungarian matching on joint positions) keeps identities and fills a vanished fighter for ≤ 0.5 s, flagged "filled".
- **Look at:** [`select()`](../src/two_fighters.py:60) (note the `img=` argument: the appearance filter only runs when you pass the frame; `REF_THR = 0.5`), [`referee_score()`](../src/referee.py:77) (0 = fighter, 1 = referee), [`skin_stats()`](../src/referee.py:51), `TwoSlotTracker.update()` in the same file.
- 🟡 **Still imperfect:** it can leave only one person, and the "tracked" percentages are an upper bound. Evidence: `research/referee/appearance/RESULTS.md` (appearance filter) and `research/pose_sweep/FINDINGS.md`.
- **Try it (about 8 s, verified, read-only):** run Stop 7b below, which prints a referee score per detected person.

### Stop 7b · `src/yolo_pose_onnx.py` 🟡: our fine-tuned pose model
- **What:** a small wrapper that runs a YOLO-pose `.onnx` file with onnxruntime only (no torch). It has the same call shape as RTMO (`model(frame) → keypoints, scores`), so it drops in anywhere. The model, `models/rncv_pose_v1.onnx`, was fine-tuned on Kaggle on public grappling/MMA images (no UFC footage). Results in `reports/finetune_rncv_pose_v1_results.md`: on public grappling images it finds both people in 89% vs 77% for the base model and almost never invents extra people. On VICOS gym footage it's still weak (35%); the real test is UFC attempts (Stop 8b).
- **Look at:** [`YoloPoseOnnx.__call__()`](../src/yolo_pose_onnx.py:39) and its `last_boxes` outputs; [`_letterbox()`](../src/yolo_pose_onnx.py:28) (resize + pad so the picture isn't squashed).
- **Try it (about 8 s, verified, read-only):**
  `$PY_RNCV -I -c "import sys; sys.path.insert(0,'src'); import cv2; from yolo_pose_onnx import YoloPoseOnnx; from referee import referee_score; cap=cv2.VideoCapture('data/clips/gsp_bisping.mp4'); cap.set(cv2.CAP_PROP_POS_FRAMES,300); f=cap.read()[1]; k,s=YoloPoseOnnx('models/rncv_pose_v1.onnx')(f); print(k.shape, [round(referee_score(f,k[i],s[i]),2) for i in range(len(k))])"` (on that frame it finds one person, score 0.14 = looks like a fighter).

### Stop 8 · `research/pose_sweep/` 🟢: how we learned the threshold was the culprit
- **What:** `sweep.py` runs RTMO on a grid of thresholds and counts how often 2+ people are found; `select2.py` is the prototype of Stop 7 (also tried and rejected a black-shirt referee rule). `FINDINGS.md` is the write-up, `results.json` the numbers.
- **Look at:** [`sweep.py main()`](../research/pose_sweep/sweep.py:39), [`select2.py select()`](../research/pose_sweep/select2.py:103).
- **Try it:** read `FINDINGS.md` section 1's table. (Re-running `sweep.py` takes minutes, skip.)

### Stop 8b · `src/pose_attempts.py` 🟢: does pose work where it matters?
- **What:** for every row in `labels.csv` whose clip is in `data/clips/`, runs pose + two-fighter selection only inside the labeled attempt window and reports coverage. Three measures: both fighters tracked, both upper bodies OK, and the new **`rnc_ok`** ("RNC-usable"): defender has head + both shoulders, attacker has head + at least one shoulder close to the defender's head. In back control the attacker's arms are hidden behind the defender, so demanding full upper bodies was too strict. The gate (PLAN 2b) is ≥ 60% usable frames. Last RTMO run: median 64% both tracked, 8 of 12 attempts pass (`reports/pose_attempts.md`).
- **Look at:** [`rnc_ok()`](../src/pose_attempts.py:33), [`window_coverage()`](../src/pose_attempts.py:50), `--model rtmo` (default) or `--model models/rncv_pose_v1.onnx` to compare the fine-tune on the same attempts, `--out` for a separate report file.
- **In/out:** `labels.csv` + clips → `reports/pose_attempts.md` (read-only on labels).
- **Try it (about 10 s, verified):** `$PY_RNCV -I -c "import sys; sys.path.insert(0,'src'); import numpy as np, pose_attempts as pa; p=np.random.rand(2,17,3); p[:,:,2]=0.9; print(pa.rnc_ok(p))"` → `True` (two fully visible skeletons). A full run takes minutes on CPU; pass `--out reports/pose_attempts_tmp.md` so you don't overwrite the report.

### Stop 8c · `research/pose_review/REVIEW.md` 🔴 (read this one!): the honest verdict on pose
- **What:** a by-eye review of 48 real frames from your labeled attempts. The "both fighters tracked" number (76–94%) only means two skeletons exist. Judged by eye, both were the *right two people* in only 1–4 of 48 frames for every pipeline. The main failure is a skeleton that spans both fighters (39–42 of 48), not the referee (3–6 of 48). In the hard frames no model proposes a clean skeleton on the choker, so selection and tracking can't fix it. Verdict: **no-go** for driving an automatic RNC signal from current pose output. Fixing one bug did help: the referee filter ignored too-dark pixels, so a black shirt looked like skin-free "fighter" (AUC 0.92 → 0.99 with a dark-aware version, saved as `referee_dark.patch`, not applied to `src/`).
- **Look at:** the table in "The eval" and "Root causes" in `REVIEW.md`; scripts `research/pose_review/eval.csv`, `render.py`, `score_roles.py`.
- **Also:** `reports/pose_attempts_finetuned.md` (fine-tuned v1: median 76% both tracked, 10/16 pass, but only 30% RNC-usable) vs `reports/pose_attempts.md` (RTMO). Read them knowing the numbers flatter the result.
- **Try it:** just read the one-screen summary at the top of `REVIEW.md` (2 min).

### Stop 8d · `research/attempt_clf/attempt_clf.py` 🟡: detecting an attempt without pose
- **What:** the workaround for Stop 8c. Frames are sampled 2 per second from every labeled clip; each frame (optionally cropped to the fighters) becomes a CLIP embedding (a general-purpose image model's "fingerprint" of the picture); a logistic regression (a simple yes/no scorer) learns "inside a labeled attempt?". Scored **leave-one-fight-out**: each fight is judged by a model that never saw it. Pooled ROC-AUC 0.66 on the full frame, **0.70** on the fighter crop, 0.72 smoothed over ~2 s; the bigger ViT-B-16 backbone is in `reports/attempt_clf_crop_b16.md`. ROC-AUC 0.5 is guessing; the roadmap wants ≥ 0.80.
- **Look at:** [`clips_and_windows()`](../research/attempt_clf/attempt_clf.py:50) (what counts as positive), [`extract()`](../research/attempt_clf/attempt_clf.py:62), [`evaluate()`](../research/attempt_clf/attempt_clf.py:116), the `--crop` / `--b16` flags. Needs its own venv (`a separate venv (clip)`) and caches features in `data/attempt_clf/`.
- **Try it:** read `reports/attempt_clf_crop.md`; per-fight AUCs range from 0.10 to 1.00, so they're noisy with this few fights. Re-running extracts CLIP features for every clip, which takes many minutes (CPU), so I haven't included a quick command.

### Stop 9 · `tools/eval_harness/` 🟢: the scoring rules, as code
- **What:** the anti-cheating rules from the plan, written so a model can't break them by accident. `splits.py`: a fight is in the test set iff a salted hash of its id is below 0.2, fixed forever; same-fighter leakage is purged. `horizons.py`: scores finish probability at 1/2/3/5/8 s after attempt start; `bell` (time ran out) is censored, not a failure; bootstrap over fights; refuses leaky columns and degenerate baselines. `events.py`: turns probabilities into attempt segments and scores them.
- **Look at:** [`lock_test_groups`/`group_cv`](../tools/eval_harness/splits.py:50), [`horizon_frame()`](../tools/eval_harness/horizons.py:82), [`horizon_metrics()`](../tools/eval_harness/horizons.py:125), [`compare_to_baseline()`](../tools/eval_harness/horizons.py:150), [`segments_from_probs()`](../tools/eval_harness/events.py:12), [`event_metrics()`](../tools/eval_harness/events.py:80).
- **In/out:** a `labels.csv` plus model predictions → AUC, Brier, CIs, event F1. Nothing real feeds it yet (no labels).
- **Try it (about 50 s measured, 11 tests pass):** `$PY_EVAL -m pytest -q -p no:cacheprovider tools/eval_harness` (11 tests).

### Stop 10 · `phase3_labels/` 🟢: where the attempts to label come from
- **What:** turns ufcstats CSVs into lists of fights to watch. `build_candidates.py`: 683 RNC finishes + 3,436 fighter-rounds with submission attempts but no submission finish. `build_fighter_priors.py`: each fighter's record **as of the day before the fight** (no peeking at their own outcome; `test_priors_leak.py` checks it). `build_queues.py`: the hybrid sampling from PREREG (successes, failures with ≤ 3 per fighter, plus a seeded `random_10`). `draw_pilot.py` and `pilot_15_RETIRED.csv` are retired.
- **Look at:** [`build_candidates.main()`](../phase3_labels/build_candidates.py:81), [`compute_priors()`](../phase3_labels/build_fighter_priors.py:66), [`take()`](../phase3_labels/build_queues.py:62). Schema: `LABEL_SCHEMA.md`; first session plan: `PILOT.md`.
- **Try it:** `$PY_RNCV -I phase3_labels/test_priors_leak.py` (if pandas missing in that venv, use `$PY_EVAL`), then open `phase3_labels/labeling_queue_successes.csv`.

### Stop 10b · `phase3_labels/qa_labels.py` 🟢: is my labeling clean?
- **What:** a read-only checker for `labels.csv` (never edits it, since the labeler may have it open). Flags duplicates, overlapping attempts, start ≥ end, finishes more than 3 s from the ufcstats finish time, missing landmark fields (unless `view_blocked`), missing `found_via`, out-of-scope fights. Rows with "compilation" in notes skip round-time checks. Writes `reports/labels_qa.md` (🔴 fix, 🟡 check, ⚪ info).
- **Look at:** [`check()`](../phase3_labels/qa_labels.py:37) (the list of rules), `LANDMARK` (the 12 fields).
- **Try it:** `$PY_CV -I phase3_labels/qa_labels.py` then open `reports/labels_qa.md`. (Not re-run for this refresh because it rewrites that report; I read the existing report: 16 attempts, 6 fights, one info-level note.)

### Stop 11 · `tools/labeler/index.html` 🟢: you, labeling
- **What:** one offline HTML page (no server, video never uploaded). Load the queue CSVs and a local clip, sync the round clock, press S at the start of the choke; the video plays 2 s and **freezes** so you code the 12 landmarks blind to the ending; then mark the end and the outcome. Writes `labels.csv` rows in LABEL_SCHEMA format. Real use so far: 16 attempts, median 1.4 min each (target was 4).
- **New keys:** <kbd>X</kbd> = view blocked (referee/cut hides the choke): skips the 12 fields and sets `view_blocked`. <kbd>G</kbd> = a state change after the 2 s landmark (body lock added, arm slides under the chin...): pauses and shows every field with the **current value highlighted**; you press a number only where something changed; stored in `state_changes`, descriptive only. For finishes the clock is anchored to the ufcstats finish time. Before every save it **re-reads `labels.csv`**, so fixes or deletions made outside the tool aren't overwritten.
- **Look at:** [`startAttempt()`](../tools/labeler/index.html:375), [`blindLock()`](../tools/labeler/index.html:238), [`saveAttempt()`](../tools/labeler/index.html:405), [`toCSV()`](../tools/labeler/index.html:206), and the X handler near [line 622](../tools/labeler/index.html:622). (Line numbers drift; search by name.)
- **Try it:** double-click the file in Chrome/Edge, load the three queue CSVs, read the on-screen key legend. Details: `tools/labeler/README.md`; judging guide: `docs/LABELING_GUIDE.md`.

### Stop 12 · `tools/overlay/` 🟢 (on fake data): the visible end product
- **What:** draws submission type, probability bar (red→green), 8 s sparkline and top-2 factors on a clip. It only uses the latest prediction at or before each frame, so it can't peek at the future. Predictions come from a CSV, so the real model plugs in later with no renderer changes.
- **Look at:** [`render()`](../tools/overlay/overlay.py:73), [`draw_panel()`](../tools/overlay/overlay.py:44), [`pred_at()`](../tools/overlay/overlay.py:38). Input format: `t_s, sub_type, prob, factors`.
- **Try it (seconds):** `cd tools/overlay` then `$PY_CV make_demo.py` and `$PY_CV overlay.py --video demo_clip.mp4 --preds demo_preds.csv --out demo_overlay.mp4`; open the mp4.

### Stop 12b · `tools/preview/corner_preview.py` 🟢: see what pose sees
- **What:** makes a preview video with the two tracked fighters in red/blue (corner guessed from glove and trunk colour near wrists and hips), each labelled with pose score and seen/filled, dropped people in thin grey, and a top bar with the running "both tracked" %. A debugging view, not a result. Modern gloves are mostly black, so many corners show "?" (guess).
- **Look at:** [`color_votes()`](../tools/preview/corner_preview.py:39), [`run_clip()`](../tools/preview/corner_preview.py:77). It reuses `two_fighters.select/TwoSlotTracker`.
- **Try it:** `$PY_RNCV -I tools/preview/corner_preview.py --clips data/clips/gsp_bisping.mp4 --stride 4` writes `data/pose/gsp_bisping_corners.mp4`. Not run for this refresh (it writes a video); roughly a minute at stride 4 (estimate).

### Stop 12c · `tools/mvp/demo.py` 🟢: the MVP 0.1 replay demo
- **What:** the first end-to-end picture. For one labeled clip it renders an overlay with a **finish % for the attacker**, a **health bar for the defender**, a live state panel and the final result (TAP / OUT COLD / ESCAPED / ...). Be clear on what is real vs stand-in: attempt windows and factors come from **your labels**, not automatic detection; the finish % comes from a small demo model (base finish rate × odds ratios for arm under chin, strong legs, defender two-on-one, ramped up with time held), fit on the *other* fights only (leave-one-fight-out), and updated live from your G-panel state changes. It never peeks at the clip's own outcome until the replay marker at the end.
- **Look at:** [`fit()`](../tools/mvp/demo.py:42), [`finish_prob()`](../tools/mvp/demo.py:60), [`state_at()`](../tools/mvp/demo.py:71), [`panel()`](../tools/mvp/demo.py:93).
- **In/out:** a clip in `data/clips/` + `phase3_labels/labels.csv` → mp4 (default `data/mvp/<clip>_demo.mp4`, git-ignored).
- **Try it (71 s, verified):** `$PY_CV -I tools/mvp/demo.py data/clips/pantoja_asakura_r2_b.mp4`, then open the mp4 in `data/mvp/`. An earlier result is already there.

### Stop 13 · `notebooks/kaggle_finetune_pose/` 🟡: teaching the pose model grappling
- **What:** a generated Kaggle GPU notebook (`build_notebook.py` creates `finetune.ipynb` and `finetune_v2.ipynb`; edit the builder, not the notebooks) that fine-tunes YOLO11m-pose on public grappling/MMA images, then exports one `.onnx`. v1 is done (`models/rncv_pose_v1.onnx`); v2 (bigger: 960 px, ~9 h) is running. `smoke_test.py` is a tiny local CPU rehearsal. **No UFC footage ever goes to Kaggle.** Walkthrough: `docs/KAGGLE_FINETUNE.md`.
- **Look at:** `docs/KAGGLE_FINETUNE.md`, then `reports/finetune_rncv_pose_v1_results.md` (base vs fine-tuned vs RTMO).
- **Try it:** read the results table. Whether v1/v2 beat RTMO on real UFC attempts is still open: run Stop 8b with `--model models/rncv_pose_v1.onnx` and `--out` set to a separate file.
- `notebooks/kaggle_yolo_pose_vicos.ipynb` is the older notebook that re-extracts VICOS keypoints with YOLO11-pose; a classifier on those keypoints scored macro-F1 0.47 vs 0.63 on the original ones.

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
- **Fine-tuning:** continuing to train an existing model on new examples (here grappling images) so it gets good at them.
- **ONNX:** a portable model file that runs on the laptop CPU without the training software.
- **View blocked:** the labeler flag when the referee, a cut or the angle hides the choke at the 2 s freeze.
- **RNC-usable (`rnc_ok`):** enough joints visible to judge a choke: defender head + both shoulders, attacker head + one shoulder close by.
- **Skin chroma:** the colour (not brightness) of skin; used to tell shirtless fighters from the black-clad referee.
- **κ (kappa):** agreement between two labelers beyond chance. 0 = chance, 1 = perfect; used to check that labels are reproducible.

---

## 4. What's real vs. planned

| Piece | Status | Notes |
|---|---|---|
| RTMO pose on laptop CPU | 🟢 | Works on 8 local clips. Needs score 0.3 / nms 0.65 |
| Referee filter (`referee.py`) | 🟡 | Skin-vs-black appearance rule inside `select()`; helps, not perfect |
| Two-fighter selection + tracking | 🔴 | "Both tracked" 64–94% but only 1–4 of 48 frames had the right two people by eye (REVIEW.md). Parked |
| Fine-tuned pose models v1/v2 | 🟡 | Beat base on public grappling images; on UFC attempts no better by eye; v2 not better than v1 |
| Position classifier (VICOS) | 🟢 | Macro-F1 0.63; weak on half guard, takedowns. Not tested on UFC footage |
| Back-control rule | 🟢 | Recall 0.78–0.83, precision 0.85 on VICOS. UFC comparison still to do |
| Attempt detector | 🟡 | `research/attempt_clf`: ROC-AUC 0.70 (0.72 smoothed), leave-one-fight-out, no pose. Target 0.80 |
| Finish-probability model | 🟡 | Only a small demo stand-in inside `tools/mvp/demo.py`. Real hazard model waits on ~150 attempts; `horizons.py` ready to score it |
| MVP 0.1 replay demo | 🟢/🟡 | Runs end to end on a labeled clip, but uses your labels for windows (see Stop 12c) |
| Eval harness | 🟢 | 11 tests pass; nothing real scored yet |
| Candidate lists, priors, queues | 🟢 | CSVs built; leak test exists |
| Labeler | 🟢 | In real use (X, G, re-read before save); median 1.4 min per attempt |
| `labels.csv` + QA | 🟡 | 36 attempts / ~20 fights, QA 0 red; goal ~150 attempts. Cap amended to 5 attacking rounds (A4) |
| Science analysis | ⚪ | PREREG frozen (v1.0, b8d817d); no analysis code until more labels exist |
| Overlay | 🟡 | Old renderer works on fake predictions; the MVP demo is the newer, nicer version |
| Corner preview | 🟢 | Debug video; corner guess often "?" |

Housekeeping: check `src/` for stray `*.tmp.*` files (one appeared before); they aren't code to read.

---

## 5. Suggested 30-minute self-tour

1. **(5 min)** Read `PROGRESS.md`, `docs/ROADMAP.md` and skim PREREG's headings. Know the question and the milestones before the code.
2. **(5 min)** Read the one-screen summary of `research/pose_review/REVIEW.md` (Stop 8c), then watch one `data/pose/*_preview.mp4`. See the mixed-skeleton problem yourself.
3. **(8 min)** Read `reports/attempt_clf_crop.md` and the top of `research/attempt_clf/attempt_clf.py` (Stop 8d). Why does a no-pose detector sidestep the problem, and why is 0.70 not enough?
4. **(7 min)** Run the MVP demo (Stop 12c) and watch the output next to your own labels for that fight. Which parts are real, which are stand-in?
5. **(5 min)** Open the labeler and `reports/labels_qa.md`. This is the bottleneck: the roadmap says labeling is the critical path.

**Your next action:** keep labeling attempts (target size is in PREREG); more labels unlock the ⚪ items.
