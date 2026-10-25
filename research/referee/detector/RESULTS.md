# Referee problem: detector route (2026-10-19)

Status: 🟢 all 3 clips scored on research/referee/eval/labels.csv. 🟡 Evidence frames are rendered in `data/referee/detector/evidence/` (local, 2x2 panels: baseline, hybrid / hybrid_ioa, topdown) but **not yet checked by eye**. Re-run:

    python -I research/referee/detector/cache_dets.py   # ~10+ min per clip, CPU
    python -I research/referee/detector/evaluate.py --evidence

## Detectors searched
| Detector | Weights | License | Used |
|---|---|---|---|
| [fight-judge YOLOv8s](https://huggingface.co/hasanfaesal/fight-judge-yolov8s) | `best.pt`, exported to ONNX (`data/referee/detector/weights/`, local) | Weights MIT. Ultralytics was used only for the one-time export (AGPL, separate venv `a separate venv (yolo)`). It runs under onnxruntime. Training data CC BY-NC-SA. | yes |
| Roboflow FightersMMA / MMA Striking | datasets only; the hosted models need a Roboflow account/API key | CC BY 4.0 (dataset) | no |
| RidgeRun MMA detector | not published | n/a | no |

## Results (all 3 clips; tracking at stride 3; label metrics on the 128 labeled frames)
| Variant | 2 tracked seen+filled (gsp / pantoja / sterling) | Both fighters kept | Referee kept | Fighters dropped | CPU fps |
|---|---|---|---|---|---|
| baseline (`two_fighters.select`) | 96 / 75 / 78% | 25/30 (83%) | **46/79 (58%)** | 4/60 (7%) | 2.3 |
| topdown (fight-judge boxes -> RTMPose-m) | 42 / 47 / 64% | 4/30 (13%) | 2/79 (3%) | 7/60 (12%) | 3.6 |
| hybrid (drop IoU < 0.3 with every fighter box) | 59 / 46 / 58% | 22/30 (73%) | **7/79 (9%)** | 8/60 (13%) | 1.5 |
| hybrid_ioa (drop if < 60% of the box lies inside a fighter box) | 65 / 45 / 61% | 23/30 (77%) | 8/79 (10%) | 7/60 (12%) | 1.5 |
| rank (box fit only ranks 3+ candidates) | 96 / 75 / 78% | 23/30 (77%) | 44/79 (56%) | 3/60 (5%) | 1.5 |

fight-judge boxes at conf >= 0.25: one box in 79 / 74 / 55% of frames (gsp / pantoja / sterling), i.e. usually one merged box around both fighters.
The "2 tracked" coverage falls under the gate partly because the baseline counted the referee as a fighter.

## What we learned
- 🔴 **The baseline keeps the referee in 58% of the labeled frames that show one.** Its high "2 tracked" coverage is inflated: the referee often fills the second slot.
- Most referee-kept frames have **only one fighter skeleton** (RTMO merges the tangled pair into one), so the pair is "mixed fighter + referee". No ranking rule can fix that, because the rule must be allowed to keep just ONE person. That is why `rank` changes nothing.
- fight-judge was trained on stand-up only. On ground grappling it draws **one merged box around both fighters** in 74–79% of frames. So top-down pose on its boxes yields one skeleton and fails (11% both kept).
- Gating RTMO people by the fighter box (hybrid_ioa) is the useful part: referee kept falls from 58% to 10%. The coverage drop is mostly honest (referee frames no longer count as "2 fighters"), but it also drops 12% of the labeled fighters (vs. 7%).
- Fighter-box fit, labeled non-small people: fighters median 0.95 (10th pct 0.59), referees median 0.09 (90th pct 0.80). So it is a strong but imperfect signal, and the ~10% of referees standing behind the pile overlap the merged box.

## Recommendation (pending a by-eye check of the evidence frames)
- Port `fighter_boxes.FighterDetector` + `gate_people(..., thr=0.6, mode="ioa")` before `two_fighters.select`. Cost: about −0.8 fps (2.3 → 1.5 on this laptop). Plain IoU 0.3 (`hybrid`) is equally good (9% vs 10% referee kept); ioa is preferred because it is robust to merged boxes.
- Combine it with the ref-appearance session's track vote: use the box gate as one feature, not a hard filter, to win back the dropped fighters.
- Don't use the top-down route until a ground-trained fighter detector exists. A Kaggle fine-tune of the YOLOv8s on Harmony4D/VICOS grappling boxes is the follow-up.

## Files
- `fighter_boxes.py`: the ONNX detector, `gate_people` (iou/ioa) and `select_fighters` (rank variant; not recommended).
- `cache_dets.py`: runs RTMO-m, fight-judge and RTMPose-m once per frame and caches the outputs to `data/referee/detector/cache/`.
- `evaluate.py`: the variants, tracking metrics, label metrics and `--evidence` 2×2 frames.
