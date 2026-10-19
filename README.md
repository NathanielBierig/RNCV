# UFC submission CV — Phase 2: BJJ position classification (VICOS)

Classify the grappling position (18 classes: e.g. `mount1` = athlete 1 on top in mount) from two athletes' pose keypoints.
This is the foundation for later phases: submissions happen *from* positions (RNC from `back`), so a position model is the first filter.

## Scripts

| File | What it does |
|---|---|
| `src/vicos_data.py` | Loads `annotations.json`, maps the 16 videos to 6 sparring sequences, builds leak-free time-block folds. Run it alone for dataset stats. |
| `src/features.py` | Turns 2×17 COCO keypoints into 178 features (normalized coordinates, joint angles, torso direction, inter-athlete distances), or 350 role-invariant features (`build_role_invariant`: canonical top-athlete-first order + symmetrized pair features, identical under athlete swap). |
| `src/train_baseline.py` | Trains + evaluates the classifier (`--model gbm` gradient boosting or `--model mlp`; `--swap-aug` = athlete-order augmentation). Writes metrics (incl. swap macro-F1 and a 10-position score with roles merged), per-class report, out-of-fold predictions and confusion matrix to `reports/`. |
| `src/back_rule.py` | Training-free back-control detector from two skeletons (facing the same way, close, chest on back, head by neck), evaluated on VICOS next to the classifiers → `reports/back_rule.md`. |
| `src/pose_smoke.py` | Phase 2b: RTMO-m pose on the laptop CPU (score_thr 0.3 / nms 0.65) over `data/clips/*.mp4`, then two-fighter selection + tracking → tracked keypoints + preview video in `data/pose/`, fps and coverage in `reports/pose_smoke.md`. |
| `src/two_fighters.py` | Picks the two fighters among detections (drops crowd, duplicates; overlap rule for the referee, *not reliable yet*) and tracks 2 identities with 0.5 s gap fill. Ported from `research/pose_sweep/select2.py`. |
| `notebooks/kaggle_yolo_pose_vicos.ipynb` | Kaggle GPU notebook: re-extracts VICOS keypoints with YOLO11-pose (optionally RTMO) in the same JSON format. |
| `DOWNLOADS.md` | Copy-paste download commands, sizes and licenses for every dataset/model. |

## Setup (Windows, no GPU)

```powershell
py -3.12 -m venv C:\Users\netan\.venvs\rncv
C:\Users\netan\.venvs\rncv\Scripts\python -m pip install -r requirements.txt
curl.exe -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
C:\Users\netan\.venvs\rncv\Scripts\python -I src/train_baseline.py --model gbm --swap-aug --tag _swapaug
C:\Users\netan\.venvs\rncv\Scripts\python -I src/back_rule.py
C:\Users\netan\.venvs\rncv\Scripts\python -I src/pose_smoke.py
```

> **Windows path-length gotcha:** a venv inside a long folder path fails to load some DLLs (`WinError 206`), so the venv lives at the short path `C:\Users\netan\.venvs\rncv`.
> The trainer uses scikit-learn's `HistGradientBoostingClassifier` (same algorithm family as LightGBM) so there's one fewer native dependency.

## How the evaluation works (and why)

- **What VICOS really is:** image id `VVFFFFF` = video `VV`, frame `FFFFF`. 16 videos = **6 sparring sequences × up to 3 phone cameras** (same-sequence cameras agree on the label at the same frame 84–100% of the time; unrelated videos 0.5%).
- **Each sequence drills only 2–4 positions** (sequence 5 is only back control, sequence 3 only turtle). So "leave one sequence out" is impossible: the test positions would never appear in training.
- **Splitting by video would leak:** the other cameras show the exact same moment.
- **What we do instead:** cut every sequence's timeline into 5 contiguous **time blocks**. Fold *k* tests on block *k* of every sequence, from all cameras at once, and drops training frames within 300 frames (~10 s) of the test block (**purge**, so near-duplicate neighbouring frames can't leak).
- **Metrics:** macro-F1 (F1 averaged equally over classes, so rare classes count as much as common ones) and balanced accuracy (average per-class recall). Both are honest under class imbalance; plain accuracy is reported only for reference.
- **Limitation:** train and test still share the same athletes, gym and session. These numbers say "the features can separate positions", **not** "this works on UFC footage". Only Phase 3+ data, split by fight, can measure that.

## Results

Full detail: `reports/TRAINING_STATUS.md`, plus `metrics_*.json`, `per_class_*.csv`, `confusion_*.png` and `back_rule.md` in `reports/`.

| Model (5 time-block folds) | Macro-F1 | Swap macro-F1 | Balanced acc. |
|---|---|---|---|
| GBM | 0.46 | 0.60 | 0.47 |
| **GBM + swap augmentation (default)** | **0.63** | **0.63** | **0.63** |
| MLP + swap augmentation | 0.58 | 0.58 | 0.58 |
| GBM, role-invariant features (`--features rolinv`) | 0.62 | 0.62 (exact) | 0.62 |
| MLP, role-invariant features | 0.59 | 0.59 (exact) | 0.59 |
| Majority-class accuracy | | | 0.14 |

- **Swap augmentation** (train on every frame twice: as-is and with the two athletes and the 1/2 label suffix swapped) gave +0.17 macro-F1 and made the model independent of athlete order, which UFC tracking needs.
- **Swap macro-F1** = score on test frames with athletes swapped. If it differs from normal macro-F1, the model is keying on *which* athlete is which (their build, the detector's ordering) instead of geometry.
- **Back control:** recall 0.78, precision 0.85. A training-free geometry rule reaches 0.83 recall where both skeletons exist (only 49% of VICOS back frames have both). Both get compared on hand-tagged UFC frames next.
- Still weak: half guard (~0.3), takedowns (~0.4), side control/mount (~0.5).

## Kaggle steps (re-extract keypoints with YOLO11-pose)

1. kaggle.com → sign in → verify your phone (Settings) so GPU + Internet are allowed.
2. **Create → New Notebook → File → Import Notebook** → upload `notebooks/kaggle_yolo_pose_vicos.ipynb`.
3. Right sidebar: **Accelerator = GPU T4 x1**, **Internet = On**.
4. **Run All**. The notebook downloads the 10 GB images itself (no upload needed). Expect ~1–1.5 h total (estimate).
5. Output panel → download `annotations_yolo11m-pose_stride1.json` → save to `data/raw/vicos_yolo/`.
6. `.venv\Scripts\python -I src/train_baseline.py --annotations data/raw/vicos_yolo/annotations_yolo11m-pose_stride1.json --tag _yolo11m`

## Reused vs built

- Checked `talhaahussain/grappling-pose-identification` (MIT): it's a binary "pin / no pin" MLP on raw keypoints with a **random frame-level split** (leaky) and YOLO-NAS weights (non-commercial license). Used as a reference only; not reused.
- No public repo trains the 18-class VICOS task with a leak-free split, so this pipeline is new.

## Licenses

VICOS: CC BY-NC-SA 4.0 (non-commercial; cite Hudovernik & Skočaj, MMSports'22). YOLO11: AGPL-3.0. RTMO/MMPose/rtmlib: Apache-2.0. Full table in `DOWNLOADS.md`.
