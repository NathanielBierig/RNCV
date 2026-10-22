# RNCV: what makes a UFC rear-naked choke finish?

RNCV = **RNC + CV** (computer vision). A UFC-only study of which rear-naked choke details predict a finish (pre-registered science), plus a live finish-probability overlay built on pose estimation.

**Quick links:** [Progress](PROGRESS.md) · [Roadmap](docs/ROADMAP.md) · [Your tasks](HUMAN_TASKS.md) · [Labeling guide](docs/LABELING_GUIDE.md) · [Picture code book](docs/rnc_codebook.html) · [Labeler](tools/labeler/index.html) · [Kaggle fine-tune guide](docs/KAGGLE_FINETUNE.md) · [Code tour](docs/CODE_TOUR.md) · [Plan](docs/PLAN.md) · [Pre-registration](research/rnc_science/PREREG.md)

---

## Where things stand

- 🟢 **Science design frozen:** [PREREG.md](research/rnc_science/PREREG.md) (v1.0 + amendments A1 men's only, A2 upper body / change log). Code book: [FACTORS.md](research/rnc_science/FACTORS.md).
- 🟡 **Labeling:** see [reports/labels_qa.md](reports/labels_qa.md) for the current count and checks. Data: [phase3_labels/labels.csv](phase3_labels/labels.csv).
- 🟡 **Pose on UFC clips:** RTMO-m + two-fighter tracking + referee filter. Coverage inside labeled attempts: [reports/pose_attempts.md](reports/pose_attempts.md). Finishes are the weak spot. The fix in progress is a pose model fine-tuned on grappling ([docs/KAGGLE_FINETUNE.md](docs/KAGGLE_FINETUNE.md)).
- 🟢 **Position classifier (VICOS):** macro-F1 0.63 on original keypoints, 0.47 on standard YOLO keypoints. Details: [reports/TRAINING_STATUS.md](reports/TRAINING_STATUS.md).

Full status: [PROGRESS.md](PROGRESS.md).

---

## How to: label attempts (your main job)

Full guide: **[docs/LABELING_GUIDE.md](docs/LABELING_GUIDE.md)**. Pictures for each answer: **[docs/rnc_codebook.html](docs/rnc_codebook.html)**.

1. **Pick a fight:** [successes queue](phase3_labels/labeling_queue_successes.csv) or [failures queue](phase3_labels/labeling_queue_failures.csv), next row with status `todo` (men's only).
2. **Get the clip** into `data\clips\` (local only, never uploaded). Ask Main for the download command if needed.
3. **Open the labeler:** `tools\labeler\index.html` in Chrome → **Ctrl+Shift+R** → *Load fight list(s) CSV* (the 3 queue files) → *Load labels.csv* → *Link labels.csv file* (both: `phase3_labels\labels.csv`).
4. **Label:** **S** start → answer the frozen 2-second panel (**X** if the view is blocked) → **G** whenever something changes → **E** at the end → outcome → Enter.
5. **Round with no RNC at all?** Tell Main "rank N watched, no RNC".
6. **Check your work:** ask Main to "run the labels QA", or run it yourself:
   ```powershell
   C:\Users\netan\.venvs\ufc-cv\Scripts\python -I phase3_labels\qa_labels.py
   ```
   Then open [reports/labels_qa.md](reports/labels_qa.md).

## How to: train the pose model on Kaggle (free GPU)

Full guide: **[docs/KAGGLE_FINETUNE.md](docs/KAGGLE_FINETUNE.md)**.

1. kaggle.com → your notebook **finetune_pose** (or import [notebooks/kaggle_finetune_pose/finetune.ipynb](notebooks/kaggle_finetune_pose/finetune.ipynb)).
2. Right sidebar → *Session options*: **GPU T4**, **Internet on**.
3. **Save Version → Save & Run All (Commit) → Save.** It runs on Kaggle's servers (about 4 h, estimate); you can close Chrome.
4. Check it any time (the Kaggle CLI is set up with your token in `C:\Users\netan\.kaggle\`):
   ```powershell
   C:\Users\netan\.venvs\ufc-cv\Scripts\kaggle kernels status nathanielbierig/finetune-pose
   ```
5. When it says **COMPLETE**, tell Main **"pull the fine-tune"**. Main downloads `rncv_pose_v1.onnx` into `models\` and re-runs the pose checks, before vs after.

Never put UFC video on Kaggle (its rules forbid it). Only open datasets (VICOS, Harmony4D) go there.

## How to: train the position classifier (laptop, CPU)

```powershell
C:\Users\netan\.venvs\rncv\Scripts\python -I src\train_baseline.py --model gbm --swap-aug --tag _swapaug
```
- Other keypoints: add `--annotations data\raw\vicos\annotations_yolo11m-pose_stride1.json --tag _swapaug_yolo11m`.
- About 30–40 min. Results land in `reports\metrics_*.json`, `per_class_*.csv`, `confusion_*.png`.

## How to: run pose on clips

```powershell
C:\Users\netan\.venvs\rncv\Scripts\python -I src\pose_attempts.py                # pose inside every labeled attempt → reports\pose_attempts.md
C:\Users\netan\.venvs\rncv\Scripts\python -I src\pose_smoke.py                   # whole clips → reports\pose_smoke.md
C:\Users\netan\.venvs\rncv\Scripts\python -I tools\preview\corner_preview.py     # red/blue skeleton preview videos → data\pose\*_corners.mp4
```

## How to: work with Claude sessions

- **Main session** (in this folder) does the work and is the only one that commits and pushes. Start a fresh one any time: it reads [CLAUDE.md](CLAUDE.md), [PROGRESS.md](PROGRESS.md) and [HUMAN_TASKS.md](HUMAN_TASKS.md) and catches up.
- **Secretary** keeps [HUMAN_TASKS.md](HUMAN_TASKS.md), [docs/BRIEF.md](docs/BRIEF.md) and [docs/DECISIONS.md](docs/DECISIONS.md) current.
- Useful phrases for Main: "run the labels QA" · "pull the fine-tune" · "swap in the fine-tuned pose model" · "next 3 failure rounds" · "rank N watched, no RNC".

---

## Repo map

| Folder | What's in it |
|---|---|
| [docs/](docs/) | Plan, decisions, brief, guides (labeling, Kaggle, footage, code tour) |
| [research/rnc_science/](research/rnc_science/) | PREREG (frozen hypotheses) and FACTORS (code book) |
| [phase3_labels/](phase3_labels/) | Fight queues, `labels.csv`, label schema, QA script |
| [src/](src/) | Pose, two-fighter tracking, referee filter, position classifier |
| [tools/](tools/) | Labeler, overlay renderer, red/blue preview, eval harness |
| [notebooks/](notebooks/) | Kaggle GPU notebooks |
| [reports/](reports/) | Every result, as markdown, JSON and plots |
| [research/](research/) | Referee study, pose sweep, critique, venture ideas |
| `data/`, `models/` | Local only (git-ignored): clips, datasets, weights |

## Setup (Windows, no GPU)

```powershell
py -3.12 -m venv C:\Users\netan\.venvs\rncv
C:\Users\netan\.venvs\rncv\Scripts\python -m pip install -r requirements.txt
curl.exe -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
```
> Venvs live at short paths (`C:\Users\netan\.venvs\...`) because a long folder path breaks some Windows DLLs. `rncv` = pose and training, `ufc-cv` = OpenCV, pandas and the Kaggle CLI.

## Position-classifier evaluation (why the numbers are honest)

- VICOS = 6 sparring sequences × up to 3 cameras. Each sequence's timeline is cut into 5 **time blocks**; each fold tests one block of every sequence (all cameras together) and drops training frames within 300 frames of it, so near-duplicate frames can't leak.
- Metrics: **macro-F1** and **balanced accuracy** (rare classes count as much as common ones); **swap macro-F1** checks the model doesn't care which athlete is "1" or "2".
- Limit: same athletes and gym in train and test, so these numbers aren't UFC performance. Only UFC data split by fight can measure that.

| Model (5 time-block folds) | Macro-F1 | Balanced acc. |
|---|---|---|
| GBM | 0.46 | 0.47 |
| **GBM + swap augmentation (default)** | **0.63** | **0.63** |
| GBM + swap aug on YOLO11m keypoints | 0.47 | 0.47 |
| MLP + swap augmentation | 0.58 | 0.58 |
| GBM, role-invariant features | 0.62 | 0.62 |
| Majority class | 0.14 accuracy | |

## Footage and licenses

- UFC footage: private local clips only, never uploaded; only derived data (keypoints, timestamps, labels) is committed. See [docs/FOOTAGE.md](docs/FOOTAGE.md).
- VICOS: CC BY-NC-SA 4.0 (cite Hudovernik & Skočaj, MMSports'22). YOLO11: AGPL-3.0. RTMO/MMPose/rtmlib: Apache-2.0. Full table: [DOWNLOADS.md](DOWNLOADS.md).
