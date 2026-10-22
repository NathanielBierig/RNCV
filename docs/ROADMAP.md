# RNCV roadmap to MVP 0.1 (as of 2026-10-22)

All times are estimates. "Sitting" = about 20–30 min of labeling.

**MVP 0.1 =** one command takes a UFC clip and outputs an overlay video: **"RNC attempt" detected automatically**, a box on the fighters, the main visible factors, and a **finish-probability bar from a model trained on your labels**. It's for private demo, not public.

| Milestone | What it needs | Done when | Effort |
|---|---|---|---|
| ✅ M0 Foundations | Plan, PREREG + amendments A1–A4, labeler, QA, queues, overlay renderer | done | — |
| 🟡 **M1 Attempt detector usable** | **~40 labeled fights** (now 20), plus longer clips with more "no attempt" footage | leave-one-fight-out ROC-AUC ≥ 0.80 (now 0.70) | ~8–10 sittings |
| ⚪ M2 First factor detector | Same image-classifier trick on fighter crops, for the easiest visible factor (body triangle, or arm under chin) | agreement with your labels well above chance (κ ≥ 0.4) | ~1 day of my work, after M1 |
| ⚪ M3 Science v1 | **~150 attempts** (now 36), second rater on ~30 | Pre-registered analysis run + short write-up ("what finishes the UFC RNC") | ~25 sittings + 1–2 days |
| ⚪ M4 Finish-probability model | Hazard model on the labels (time + factors), calibrated | probability calibrated on held-out fights | ~1 day, after M3 data |
| ⚪ **MVP 0.1** | M1 + M2 + M4 wired into the existing renderer; **design options first** (owner: "gnarly, sciency, colorful but minimal") | runs end to end on a held-out clip | ~2–3 days |
| ⏸️ Parked | Precise skeletons (pose merges tangled fighters; 4/48 correct). Revisit with a different kind of pose model later | — | — |

**The critical path is labeling.** M1, M3 and M4 all wait on it; everything else is a day or two of my work each.
