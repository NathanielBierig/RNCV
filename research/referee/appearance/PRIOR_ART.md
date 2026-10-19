# Prior art: dropping the referee in combat-sport CV (searched 2026-10-19, ~15 min)

Short answer: **no public MMA/boxing/wrestling repo drops the referee from a pose pipeline.** Projects either train a fighter-only detector or ignore the problem. The pieces we can reuse come from soccer (referee/team classification) and fencing.

| Source | What it does | License | Reusable for RNCV? |
|---|---|---|---|
| [fight-judge](https://github.com/hasanfaesal/fight-judge) / [HF weights](https://huggingface.co/hasanfaesal/fight-judge-yolov8s) | UFC fighter-only YOLOv8s detector (no referee class), stand-up frames | MIT code/weights; data CC BY-NC-SA; Ultralytics runtime AGPL | Being tested by the ref-detector session. Ground frames are out of its training data. |
| [RidgeRun: MMA fighter detection](https://ridgerun.com/post/mma-fighter-detection) | Blog: generic person detectors return audience and referee boxes, so they trained a fighter detector | Commercial, no code | Confirms the problem; nothing to reuse. |
| [MMA Fighter Pose dataset (Mendeley)](https://data.mendeley.com/datasets/c456bnk8bm/2) | COCO-17 keypoints for UFC stand-up fighters | See page (Mendeley data, usually CC BY 4.0) | Possible fighter-only training data; stand-up only. |
| [FERA, fencing (arXiv 2509.18527)](https://arxiv.org/pdf/2509.18527) | RTMDet + RTMPose; drops referees with geometry rules (tracks low in the frame / off the piste) + size/confidence filters | Paper | Geometry rules don't transfer: the MMA referee walks around the cage and stands over the fighters. |
| [Roboflow Universe boxing sets](https://universe.roboflow.com/martas-workspace/experiment-1_boxing) | Detector datasets with a "Boxing Referee" class | CC BY 4.0 (Experiment 1_Boxing) | Small, undocumented, boxing (referee wears a white shirt). Low value. |
| [roboflow/sports](https://github.com/roboflow/sports) (soccer) | Team/referee split: SigLIP embeddings of player crops → UMAP → KMeans, per track | MIT | **The idea is reusable**: embed crops with a CLIP-family model, then cluster/vote per track. Same as our method 3a + 3c. |
| [CLIP-ReIdent (arXiv 2303.11855)](https://arxiv.org/pdf/2303.11855) | CLIP zero-shot prompts on sports person crops (jersey colour) | Paper | Confirms CLIP prompts on clothing work on broadcast crops. |
| Koshkina et al., via [arXiv 2502.21242](https://arxiv.org/pdf/2502.21242) | Trained referee-vs-player classifier before team embedding | Paper | Shows a small trained classifier is the standard approach once you have labels (we have ~our eval set). |
| Skin-pixel detection (YCrCb / HSV rules, e.g. Kovac 2003; Chai & Ngan 1999) | Classic colour thresholds for skin | Textbook | Basis for method 3b. Known weakness on dark skin and coloured lighting, which is why we add texture/saturation cues. |

Takeaways for this study:
- The soccer pattern (CLIP-family embedding per crop, then decide per track) is the closest proven recipe. That is methods 3a + 3c.
- MMA has an advantage soccer doesn't: the fighters are shirtless and the referee is fully dressed, so a clothing cue (3b) is physically well-founded.
- A "referee" class detector for MMA doesn't exist publicly.
