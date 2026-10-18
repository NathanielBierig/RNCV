# UFC submission CV — Phase 2: BJJ position classification (VICOS)

Classify the grappling position (18 classes: e.g. `mount1` = athlete 1 on top in mount) from two athletes' pose keypoints.
This is the foundation for later phases: submissions happen *from* positions (RNC from `back`), so a position model is the first filter.

## Scripts

| File | What it does |
|---|---|
| `src/vicos_data.py` | Loads `annotations.json`, maps the 16 videos to 6 sparring sequences, builds leak-free time-block folds. Run it alone for dataset stats. |
| `src/features.py` | Turns 2×17 COCO keypoints into 178 features: normalized coordinates, joint angles, torso direction, inter-athlete distances. |
| `src/train_baseline.py` | Trains + evaluates the classifier (`--model gbm` gradient boosting or `--model mlp`), writes metrics, per-class report and confusion matrix to `reports/`. |
| `notebooks/kaggle_yolo_pose_vicos.ipynb` | Kaggle GPU notebook: re-extracts VICOS keypoints with YOLO11-pose (optionally RTMO) in the same JSON format. |
| `DOWNLOADS.md` | Copy-paste download commands, sizes and licenses for every dataset/model. |

## Setup (Windows, no GPU)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
curl.exe -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
.venv\Scripts\python -I src/vicos_data.py
.venv\Scripts\python -I src/train_baseline.py --model gbm
```

> **Windows path-length gotcha:** inside the Claude app's session folder the real path is very long, so LightGBM/OpenCV DLLs fail to load (`WinError 206`).
> That's why the trainer uses scikit-learn's `HistGradientBoostingClassifier` (same algorithm family as LightGBM). In a normal folder like `C:\Users\netan\projects\...` this isn't an issue.

## How the evaluation works (and why)

- **What VICOS really is:** image id `VVFFFFF` = video `VV`, frame `FFFFF`. 16 videos = **6 sparring sequences × up to 3 phone cameras** (same-sequence cameras agree on the label at the same frame 84–100% of the time; unrelated videos 0.5%).
- **Each sequence drills only 2–4 positions** (sequence 5 is only back control, sequence 3 only turtle). So "leave one sequence out" is impossible: the test positions would never appear in training.
- **Splitting by video would leak:** the other cameras show the exact same moment.
- **What we do instead:** cut every sequence's timeline into 5 contiguous **time blocks**. Fold *k* tests on block *k* of every sequence, from all cameras at once, and drops training frames within 300 frames (~10 s) of the test block (**purge**, so near-duplicate neighbouring frames can't leak).
- **Metrics:** macro-F1 (F1 averaged equally over classes, so rare classes count as much as common ones) and balanced accuracy (average per-class recall). Both are honest under class imbalance; plain accuracy is reported only for reference.
- **Limitation:** train and test still share the same athletes, gym and session. These numbers say "the features can separate positions", **not** "this works on UFC footage". Only Phase 3+ data, split by fight, can measure that.

## Results

RESULTS_PLACEHOLDER

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
