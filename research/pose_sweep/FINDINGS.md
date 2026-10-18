# Pose on UFC chokes: what's wrong and what fixes it (2026-10-19, overnight)

Clips: `data/clips/` gsp_bisping (24 s), pantoja_asakura_r2 (31 s), sterling_sandhagen (64 s). All three are chokes ±5 s (per the user). Model: RTMO-m (rtmlib, CPU). No manual labels were used.

## 1. The second fighter is lost to RTMO's *confidence* cutoff, not to overlap

`sweep.py`, every 15th frame. "2+ upper" = 2+ people with ≥ 5 of 7 upper-body joints (nose, shoulders, elbows, wrists) at conf ≥ 0.3.

| score_thr | nms_thr | gsp_bisping 2+ det / 2+ upper | pantoja 2+ det / 2+ upper | sterling 2+ det / 2+ upper | 3+ det (junk) |
|---|---|---|---|---|---|
| 0.7 (default) | 0.45 (default) | 38% / 27% | 26% / 6% | 16% / 5% | 0–8% |
| 0.7 | 0.85 | 38% / 27% | 26% / 6% | 17% / 6% | 0–8% |
| 0.5 | 0.65 | 73% / 44% | 60% / 16% | 63% / 26% | 3–23% |
| **0.3** | **0.65** | **92% / 75%** | **73% / 37%** | **86% / 52%** | 31–65% |
| 0.3 | 0.85 | same as 0.65 | | | |

- Loosening the overlap filter alone does **nothing**. The tangled second fighter is detected, but with low confidence (< 0.7), and the default cutoff throws it away.
- At **score 0.3 / nms 0.65**, the second fighter is present in 73–92% of frames. The price is junk detections: the referee, crowd and duplicate skeletons. Section 2 filters them out automatically.
- `src/pose_smoke.py` hard-codes the defaults (0.7 / 0.45). **It should be changed to 0.3 / 0.65 plus the selection step** (build-phase2 owns that file).

## 2. Automatic two-fighter selection (`select2.py`, no labels)

The rules: drop the crowd (small boxes); drop duplicate skeletons; with 3+ left, keep the most-overlapping pair (referee heuristic, see below); track 2 identities; **fill gaps of up to 0.5 s** from the last pose (flagged as filled).

Every 5th frame, score 0.3 / nms 0.65:

| Clip | Raw 2+ people | 2 fighters kept | 2 kept, both upper bodies OK | 2 tracked (seen) | 2 tracked (seen or filled ≤ 0.5 s) |
|---|---|---|---|---|---|
| gsp_bisping | 93% | 88% | 59% | 88% | **97%** |
| pantoja_asakura_r2 | 71% | 51% | 26% | 51% | **64%** |
| sterling_sandhagen | 88% | 63% | 41% | 63% | **73%** |

Defaults gave 0–23% for "2 people with ≥ 12/17 joints".

**The referee rule is NOT solved; I checked it by eye on the saved evidence frames** (`data/pose/select2/*.jpg`: red = dropped, green = kept):
- **Rule A, black-shirt colour** (dark torso, also vs. own forearms, upright): **rejected.** It dropped *fighters* in shadow and dark-skinned fighters (e.g. Sterling) and kept the real referee, whose sleeves are black too.
- **Rule B, keep the most-overlapping pair** (the current code): right in the pantoja frames, **wrong** in sterling frame 195 (a sprawled fighter's box overlaps the referee's, so the referee was kept and Sterling dropped). GSP is mixed.
- So the "2 fighters kept" numbers above are an **upper bound**: some frames hold the referee instead of a fighter.
- **Fix that should work, still to test:** a detector trained on *fighters only*, e.g. [fight-judge YOLOv8s](https://huggingface.co/hasanfaesal/fight-judge-yolov8s) (MIT weights, 5 k UFC frames, no referee class), used as the top-down box source for RTMPose. Alternatively, appearance tracking: the referee wears black **trousers and shirt** for the whole clip, so one bad frame is outvoted by many.

Gap filling ("fill in the blanks") adds +9 to +13 points of two-fighter coverage at 0.5 s.

## 3. Better models and data for close contact (searched; nothing downloaded)

| Resource | What | License | Use for us |
|---|---|---|---|
| [Harmony4D](https://jyuntins.github.io/harmony4d/) (NeurIPS 2024, CMU) | 1.66 M images of close human contact: **grappling, MMA**, wrestling, hugging. Boxes, tracking, 2D/3D pose, 20+ cameras. [HF data](https://huggingface.co/datasets/Jyun-Ting/Harmony4D), [code](https://github.com/jyuntins/harmony4d) | MIT (HF card + repo) | **The best fine-tuning set for tangled fighters.** It's 352 GB, so download only the grappling/MMA sequences and fine-tune RTMO/RTMPose on Kaggle GPU. One blog reports a ViTPose fine-tune on a Harmony4D subset at 0.649 AP (couldn't verify; the page is now 404). |
| [VICOS BJJ](https://vicos.si/resources/jiujitsu/) (already in `data/raw/vicos`) | 120 k BJJ frames, **both athletes' keypoints**, incl. 13 k back-control frames | CC BY-NC-SA | A second fine-tuning set with real gi/no-gi grappling. Needs `images.zip` (size unknown). Its keypoints were auto-detected then verified, so they're decent pseudo-labels. |
| [fight-judge](https://github.com/hasanfaesal/fight-judge) | UFC **fighter-only** detector (YOLOv8s, no referee class) + YOLO11x-pose fine-tuned on 5 k UFC frames | Code/models MIT; data CC BY-NC-SA | A detector that ignores the referee by design. **But** the frames are stand-up only, and its pose labels came from YOLO itself, so expect little gain on the ground. Ultralytics runtime = AGPL. |
| [BUCTD](https://github.com/amathislab/BUCTD) (ICCV 2023) | Bottom-up proposals condition a top-down model; built for crowds and occlusion (+7.8% on OCHuman) | Check LICENSE | Strong method for overlapping people, but research code and heavier. Use only if the steps above fall short. |
| [ErayAmath/Bjj-Position](https://github.com/ErayAmath/Bjj-Position) | BJJ pose → tracking → MLP → Viterbi timeline on VICOS; 43.2% over 18 classes on a held-out camera | (check) | A sanity reference for our 0.63 macro-F1. Its Viterbi smoothing is worth copying for position timelines. |

**More RNC data:** no public dataset has labeled RNC attempts. The closest are VICOS's back class (one athlete pair) and Harmony4D's grappling sequences (no submission labels). The labeled UFC set from Phase 3 stays the only RNC outcome data, which is why the science study is the project's original contribution.

## 4. Recommendation (no manual marking needed)

1. **Now, free:** switch pose to score 0.3 / nms 0.65 + `select2` crowd/duplicate filtering and 0.5-s gap filling (build-phase2: port into `src/pose_smoke.py`).
1b. **Referee:** test the fight-judge fighter-only detector as the box source (it needs the Ultralytics runtime, AGPL, fine for research; or export to ONNX). Score it on the saved evidence frames.
2. **Next, if two-fighter upper-body coverage is still under the 60% gate:** fine-tune RTMO-m on **VICOS images + Harmony4D grappling/MMA sequences** on a Kaggle GPU, which needs the user to download the data and upload it to Kaggle. These are datasets, not UFC video. No hand labels.
3. **Keep separate:** the science study uses hand-coded factors and does not depend on any of this.
