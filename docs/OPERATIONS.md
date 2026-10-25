# RNCV operations (internal how-tos)

Day-to-day steps for the owner and the Claude sessions. The public overview is in [README.md](../README.md).

## How to: label attempts (your main job)

Full guide: **[docs/LABELING_GUIDE.md](LABELING_GUIDE.md)**. Pictures for each answer: **[docs/rnc_codebook.html](rnc_codebook.html)**.

1. **Pick a fight:** [successes queue](../phase3_labels/labeling_queue_successes.csv) or [failures queue](../phase3_labels/labeling_queue_failures.csv), next row with status `todo` (men's only).
2. **Get the clip** into `data\clips\` (local only, never uploaded). Ask Main for the download command if needed.
3. **Open the labeler:** `tools\labeler\index.html` in Chrome → **Ctrl+Shift+R** → *Load fight list(s) CSV* (the 3 queue files) → *Load labels.csv* → *Link labels.csv file* (both: `phase3_labels\labels.csv`).
4. **Label:** **S** start → answer the frozen 2-second panel (**X** if the view is blocked) → **G** whenever something changes → **E** at the end → outcome → Enter.
5. **Round with no RNC at all?** Tell Main "rank N watched, no RNC".
6. **Check your work:** ask Main to "run the labels QA", or run it yourself:
   ```powershell
   python -I phase3_labels\qa_labels.py
   ```
   Then open [reports/labels_qa.md](../reports/labels_qa.md).

## How to: train the pose model on Kaggle (free GPU)

Full guide: **[docs/KAGGLE_FINETUNE.md](KAGGLE_FINETUNE.md)**.

1. kaggle.com → your notebook **finetune_pose** (or import [notebooks/kaggle_finetune_pose/finetune.ipynb](../notebooks/kaggle_finetune_pose/finetune.ipynb)).
2. Right sidebar → *Session options*: **GPU T4**, **Internet on**.
3. **Save Version → Save & Run All (Commit) → Save.** It runs on Kaggle's servers (about 4 h, estimate); you can close Chrome.
4. Check it any time (the Kaggle CLI is set up with your token in `~/.kaggle/`):
   ```powershell
   kaggle kernels status nathanielbierig/finetune-pose
   ```
5. When it says **COMPLETE**, tell Main **"pull the fine-tune"**. Main downloads `rncv_pose_v1.onnx` into `models\` and re-runs the pose checks, before vs after.

Never put UFC video on Kaggle (its rules forbid it). Only open datasets (VICOS, Harmony4D) go there.

## How to: train the position classifier (laptop, CPU)

```powershell
python -I src\train_baseline.py --model gbm --swap-aug --tag _swapaug
```
- Other keypoints: add `--annotations data\raw\vicos\annotations_yolo11m-pose_stride1.json --tag _swapaug_yolo11m`.
- About 30–40 min. Results land in `reports\metrics_*.json`, `per_class_*.csv`, `confusion_*.png`.

## How to: run pose on clips

```powershell
python -I src\pose_attempts.py                # pose inside every labeled attempt → reports\pose_attempts.md
python -I src\pose_smoke.py                   # whole clips → reports\pose_smoke.md
python -I tools\preview\corner_preview.py     # red/blue skeleton preview videos → data\pose\*_corners.mp4
```

## How to: work with Claude sessions

- **Main session** (in this folder) does the work and is the only one that commits and pushes. Start a fresh one any time: it reads [CLAUDE.md](../CLAUDE.md), [PROGRESS.md](../PROGRESS.md) and [HUMAN_TASKS.md](../HUMAN_TASKS.md) and catches up.
- **Secretary** keeps [HUMAN_TASKS.md](../HUMAN_TASKS.md), [docs/BRIEF.md](BRIEF.md) and [docs/DECISIONS.md](DECISIONS.md) current.
- Useful phrases for Main: "run the labels QA" · "pull the fine-tune" · "swap in the fine-tuned pose model" · "next 3 failure rounds" · "rank N watched, no RNC".

## Position classifier evaluation (VICOS, side experiment)

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
