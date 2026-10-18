# Footage decision (2026-10-18)

**Decision: UFC only.** No gym footage and no other promotions for now.

**Why:** UFC is the highest level of the sport, so whether a choke finishes comes down to pure technique against elite defense, not a skill gap. That is the point of the science-based RNC study.

## How UFC footage is used (not legal advice)

| Use | Source | Copies? |
|---|---|---|
| Watching + hand labeling (timestamps, outcome, factors, style tags) | Legitimate streams: UFC Fight Pass, UFC's official free fights on YouTube | No copies needed |
| Pose extraction / CV (Phases 2b, 4, 5b, 6) | Private local clips of individual attempts, kept on the laptop only | **Yes: a personal-research risk the user accepts knowingly** (download breaks YouTube/Fight Pass terms) |

## Rules

- Raw video never goes into git, Kaggle (its AUP bans uploading infringing data, even privately), cloud drives or social media. `.gitignore` already blocks `*.mp4`, `*.mov` and `*.avi`.
- Clip only the attempt (about 10 s before the start to the end). No full fights.
- Pose runs on the **laptop CPU** for these clips (RTMO-m via rtmlib/ONNX; expect about 1–3 fps, an estimate to measure in Phase 2b). A 40 s attempt clip at 30 fps is 1,200 frames, so a few minutes per clip. Kaggle GPU is only for non-UFC data (e.g. VICOS).
- Only **derived data** is kept in the repo and shared: keypoints, timestamps, labels, stats, plots.
- The overlay demo on UFC clips stays private (portfolio interviews, shown live). Public posts use only derived visuals, e.g. skeleton-only renders on a blank background plus charts.
