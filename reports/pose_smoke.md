# Pose smoke test (Phase 2b)

Model: RTMO-m (rtmlib + onnxruntime, CPU). Machine: Intel64 Family 6 Model 140 Stepping 1, GenuineIntel. Joint counted as confident if score >= 0.3; a person 'passes' with >= 12 of 17.

| Clip | Frames processed (stride) | CPU fps | % frames 2+ people pass | 1+ | 3+ (ref visible?) | Mean people (>= 1 confident joint) |
|---|---|---|---|---|---|---|
| demo_clip | 360 of 360 (1) | 2.78 | 0.0% | 0.0% | 0.0% | 0.00 |

**How to read it:** '2+ people pass' is an upper bound on 'both fighters tracked', since the referee can be one of the two.
Open `data/pose/<clip>_preview.mp4` and check that the skeletons sit on the fighters during the RNC.
At 2.8 fps, a 60 s clip at 30 fps with stride 3 takes about 4 min on this CPU.
