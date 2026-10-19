# Pose smoke test (Phase 2b)

Latest run of `src/pose_smoke.py`. Model: RTMO-m (rtmlib + onnxruntime, CPU), score_thr 0.3, nms_thr 0.65, then two-fighter selection + 2-slot tracking with gap fill up to 0.5 s. Machine: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel.

| Clip | Frames processed (stride) | CPU fps | 2+ raw detections | 2 fighters kept, both >= 12/17 joints | 2 kept, both upper bodies OK | 2 tracked (seen) | 2 tracked (seen or filled) | Dropped crowd / dup / ref |
|---|---|---|---|---|---|---|---|---|
| gsp_bisping | 240 of 720 (3) | 2.43 | 92% | 26% | 30% | 38% | 65% | 308 / 122 / 30 |
| pantoja_asakura_r2 | 309 of 925 (3) | 2.58 | 74% | 14% | 15% | 16% | 42% | 58 / 123 / 0 |
| sterling_sandhagen | 640 of 1919 (3) | 3.17 | 88% | 27% | 33% | 42% | 66% | 244 / 223 / 47 |

**How to read it:** "kept" and "tracked" are upper bounds on *fighter* coverage. Referee removal is not solved, so some kept people are the referee. Open `data/pose/<clip>_preview.mp4` (orange/cyan = fighter slots, thin = filled from the last pose, red dots = dropped people) and check by eye.
Upper body OK = at least 5 of 7 upper-body joints (nose, shoulders, elbows, wrists) confident, which is what an RNC needs.
Before this change (RTMO defaults 0.7 / 0.45, no selection), the >= 12/17 column was 23% / 0% / 1% for gsp_bisping / pantoja_asakura_r2 / sterling_sandhagen (see the notes below).

## First UFC run, 2026-10-19 (chief-of-staff, overnight)

The clips in `data/clips/` are **gsp_bisping, pantoja_asakura_r2 and sterling_sandhagen** (24 s, 31 s and 64 s, 1080p, 29.97 fps). These are *not* the expected duplessis_adesanya_r4 / oliveira_gamrot_r2 / allen_duncan_r5. They're short attempt clips, so most frames are back control or the choke itself; there are no labels yet to cut out the exact choke window.

**Answer to "how often are 2+ people tracked during the choke": rarely.** Sensitivity, from `data/pose/<clip>.npz` (stride 3):

| Clip | 2+ detections (any confidence) | 2+ with ≥ 6/17 joints | ≥ 8 | ≥ 10 | ≥ 12 (table above) | 2+ with ≥ 5/7 upper-body joints |
|---|---|---|---|---|---|---|
| gsp_bisping | 36.7% | 35.8% | 31.2% | 27.5% | 22.9% | 25.4% |
| pantoja_asakura_r2 | 26.9% | 21.7% | 13.9% | 4.9% | 0.0% | 8.4% |
| sterling_sandhagen | 16.1% | 11.6% | 10.9% | 3.9% | 1.1% | 5.8% |

2+ detections per 5-s bin (shows when tracking holds):
- gsp_bisping: 52, 4, 28, 68, 30%
- pantoja_asakura_r2: 12, 28, 40, 4, 24, 42, 89%
- sterling_sandhagen: 0, 4, 22, 26, 0, 16, 12, 36, 0, 0, 10, 40, 50%

**Reading:**
- The joint threshold isn't the main problem. Even at *any* confidence, the second person is missing in 63–84% of frames. RTMO usually returns **one** person for two tangled fighters.
- A likely cause is RTMO's own defaults: `score_thr 0.7`, and `nms_thr 0.45`, which deletes a box overlapping another by > 45%. Back-control boxes overlap heavily. `research/pose_sweep/` re-runs the clips over a grid of these thresholds **Results: [research/pose_sweep/FINDINGS.md](../research/pose_sweep/FINDINGS.md).** In short, the cutoff is the culprit: score_thr 0.3 lifts two-person frames to 73–92%. Automatic referee removal is not solved yet.
- By the PLAN 2b gate (≥ 60% usable frames during back control), **this is a no-go with default settings.** Don't spend labeling hours on pose-dependent work until the sweep or a fallback (top-down detector + RTMPose, or fine-tuning on corrected frames) passes.
- The science study (hand-labeled factors) is **not affected**. It needs no pose.
