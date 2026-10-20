# RNCV progress (as of 2026-10-20 evening)

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## ▶ Next session starts here
1. **Check the Kaggle fine-tune:** `C:\Users\netan\.venvs\ufc-cv\Scripts\kaggle kernels status nathanielbierig/finetune-pose`. If COMPLETE: `kaggle kernels output nathanielbierig/finetune-pose -p models\` → plug `rncv_pose_v1.onnx` in (see [docs/KAGGLE_FINETUNE.md](docs/KAGGLE_FINETUNE.md)) → re-run `src\pose_attempts.py` with the new model and compare with [reports/pose_attempts.md](reports/pose_attempts.md). Then re-extract the VICOS keypoints with it and retrain the classifier (was 0.47 with standard YOLO).
2. **Labeling continues** (owner): next failure rounds + successes. Run the QA after each sitting.
3. **Open decision for the owner:** the PREREG cap "max 3 attempts per attacker/defender" clashes with "label every attempt in a watched round" (Blachowicz has 5 attempts in one round, Oliveira 4). Proposed amendment: the cap counts **fights per fighter (max 3)**, not attempts. Needs the owner's OK.
4. The owner must **reload the labeler** (Ctrl+Shift+R) to get the fix that re-reads `labels.csv` before every save.

## Decisions
- 🟢 Direction: science-based RNC + live overlay. UFC only, men's divisions only (A1). Clips local only.
- 🟢 PREREG v1.0 frozen (`b8d817d`) + A1 (men's only) + A2 (upper_body, change log = descriptive / hazard only).
- 🟢 Code book: [FACTORS.md](research/rnc_science/FACTORS.md); human guide: [LABELING_GUIDE.md](docs/LABELING_GUIDE.md) + [picture code book](docs/rnc_codebook.html).

## Phase status
| Phase | Status |
|---|---|
| 1. Resource search | 🟢 |
| 2. Position classifier (VICOS) | 🟢 GBM + swap aug 0.63 macro-F1 (original keypoints); 🟡 0.47 on YOLO11m keypoints (YOLO finds both athletes in only 46% of frames) |
| 2b. Pose on UFC | 🟡 RTMO-m + two-fighter tracker + skin/clothing referee filter. Labeled attempts: median 64% both-fighters coverage; finishes worst (33–46%). Fine-tune running on Kaggle. |
| 3. Labeling | 🟡 16 attempts / 6 fights (7 finish-list, 9 failure-round) + 1 watched negative round (Pimblett–Leavitt R1). Moreno–Royval R1 skipped (clip failed). QA clean. ~1.5 min per attempt. |
| 4. Attempt detection | ⚪ needs ~100+ labeled attempts |
| 5. Finish prediction + science | ⚪ design frozen; options memo [DECISION_PHASE5_6.md](docs/DECISION_PHASE5_6.md) |
| 6. Overlay | 🟡 renderer + red/blue preview tool |
| 7. Expansion | ⚪ |

## Tools that exist
Labeler (S/E, blind 2-s panel, X blocked view, G state changes with the current value highlighted, clock anchored to the known finish, side panel, refuses queue files, re-reads the file before saving) · labels QA · pose-on-attempts report · red/blue preview · overlay renderer · eval harness · Kaggle CLI (token set).

## Where to read more
[README](README.md) (how-tos) · [CODE_TOUR](docs/CODE_TOUR.md) · [BRIEF](docs/BRIEF.md) · [HUMAN_TASKS](HUMAN_TASKS.md) · [research/referee/](research/referee/) · [research/pose_sweep/FINDINGS.md](research/pose_sweep/FINDINGS.md)
