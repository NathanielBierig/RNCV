# Referee eval set (hand-labeled, 2026-10-19)

A small labeled set for scoring any method that has to tell the **referee** apart from the **fighters** among RTMO detections. The appearance session (research/referee/appearance/) and the detector session both use it.

## How it was made
1. `extract.py`: RTMO-m (rtmlib, CPU) at **score_thr 0.3 / nms_thr 0.65** (the `src/pose_smoke.py` settings) on **every 5th frame** of the 3 clips in `data/clips/`. All raw detections are cached in `data/referee/dets/<clip>.npz` (`frame_idx`, `kpts` [object array of N×17×2], `scores` [N×17], `fps`).
2. Eval frames: 40 evenly spread over each clip, **plus** the frames in `data/pose/select2/` (incl. sterling 195). That gives 128 frames (gsp_bisping 40, pantoja_asakura_r2 44, sterling_sandhagen 44) and 399 detected people.
3. `sheets.py` drew one labeling sheet per frame (skeletons, numbered boxes, crops). **Every person was labeled by eye** from those sheets (`data/referee/raw_labels.txt`). `build_labels.py` turns those labels into `labels.csv`.

Local-only files (git-ignored, never upload): `data/referee/frames/<clip>_<frame>.jpg` (full frames), `crops/<clip>_<frame>_<idx>.jpg`, `label_sheets/`, `dets/`.

## labels.csv columns
| column | meaning |
|---|---|
| clip, frame | clip stem and **raw video frame index** (0-based, as read by OpenCV) |
| person_idx | index in RTMO's raw output order for that frame (the order of `kpts`/`scores` in `dets/<clip>.npz`, **before** `select()` re-sorts) |
| x0, y0, x1, y1 | box in full-frame pixels: confident joints (≥ 0.3) plus 10% padding, clipped to the frame. RTMO's own box isn't returned by rtmlib. |
| label | `fighter`, `referee`, `duplicate` (a second skeleton of a body already labeled; notes say which), `crowd_or_junk` (crowd, cage-side officials, camera occluders) |
| small_box | 1 if the box area is < 15% of the largest in the frame, i.e. `two_fighters.select()`'s crowd rule already drops it |
| mean_kpt_score | mean of the 17 joint scores |
| notes | free text, mostly frame-level (e.g. "top fighter not separately detected") |

## Counts
| label | all | not small_box (what the referee step actually sees) |
|---|---|---|
| fighter | 152 | 152 |
| referee | 99 | **79** (gsp 37, pantoja 22, sterling 20) |
| duplicate | 68 | 68 |
| crowd_or_junk | 80 | 7 |

## Labeling conventions and caveats (read before scoring)
- Tangled fighters often come out as **one skeleton mixing both bodies**. Such a skeleton is labeled `fighter` (it's fighter pixels). When two skeletons cover the same mix, the better-looking one is `fighter` and the other `duplicate`.
- "Duplicate" was judged by eye (same body), not by the `_same_body` rule; some duplicates survive `select()`.
- A referee seen only as legs/shoes/glove at a frame edge is still `referee`. Most of those are `small_box = 1`.
- One labeler (Claude), no second rater. Borderline calls: fighter-vs-duplicate on mixed skeletons (~10 cases). Referee-vs-not is unambiguous in every frame (black shirt and trousers, gloves).
- Only 3 clips and 3 referees (2 of them bald men in black). Expect optimism vs. new events.

## Suggested metrics
- Per person (non-small boxes): precision/recall of "referee".
- Per frame: **"both fighters kept"**: after the method + `select()`, the 2 kept people are both `fighter`, among frames with ≥ 2 labeled fighters (gsp 14, pantoja 11, sterling 17 frames; see `appearance/RESULTS.md` for the exact denominators). Also report "referee kept" = any kept person is `referee`.
