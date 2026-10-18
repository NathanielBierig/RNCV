# Pose smoke test (Phase 2b)

Model: RTMO-m (rtmlib + onnxruntime, CPU). Machine: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel. Joint counted as confident if score >= 0.3; a person 'passes' with >= 12 of 17.

| Clip | Frames processed (stride) | CPU fps | % frames 2+ people pass | 1+ | 3+ (ref visible?) | Mean people (>= 1 confident joint) |
|---|---|---|---|---|---|---|
| gsp_bisping | 240 of 720 (3) | 2.56 | 22.9% | 61.7% | 0.8% | 1.24 |
| pantoja_asakura_r2 | 309 of 925 (3) | 2.57 | 0.0% | 72.8% | 0.0% | 1.08 |
| sterling_sandhagen | 640 of 1919 (3) | 2.34 | 1.1% | 58.3% | 0.0% | 0.91 |

**How to read it:** '2+ people pass' is an upper bound on 'both fighters tracked', since the referee can be one of the two.
Open `data/pose/<clip>_preview.mp4` and check that the skeletons sit on the fighters during the RNC.
At 2.5 fps, a 60 s clip at 30 fps with stride 3 takes about 4 min on this CPU.

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
