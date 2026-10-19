# RNCV progress (as of 2026-10-19)

🟢 done · 🟡 in progress · 🔴 blocker / needs the owner · ⚪ not started

## Decisions
- 🟢 Direction: science-based RNC (what makes a choke finish) + live finish-probability overlay.
- 🟢 UFC only (`docs/FOOTAGE.md`): clips stay local, only derived data is kept.
- 🟢 **PREREG v1.0 frozen** at commit `b8d817d`: 3 hypotheses (arm under chin, body triangle/two hooks, defender two-on-one), hybrid sampling with max 3 attempts per fighter, bell = censored.
- 🟢 Code book v2 (`research/rnc_science/FACTORS.md`): RNC style tags (incl. Dagestani `wrist_pull`), multi-tag style sequence, exploratory factors.

## Phase status
| Phase | Status |
|---|---|
| 1. Resource search | 🟢 done |
| 2. Position classifier (VICOS) | 🟢 GBM + swap augmentation, macro-F1 **0.63** (default). Role-invariant variant 0.62. VICOS "Back" comes from one session only, so it can't validate UFC. |
| 2b. Pose on UFC clips | 🟡 RTMO-m at score 0.3 / nms 0.65 + two-fighter tracker + **skin/clothing referee filter** (referee wrongly kept 58% → 10% on a 399-person eval set). Real two-fighter coverage (seen or filled) is 65 / 42 / 66% on the 3 test clips. That's below the 60% gate on Pantoja, so the next step is **fine-tuning on grappling data** (Kaggle notebook in prep). |
| 3. Labeling | 🟡 Queues ready (315 successes capped per fighter, failures, random 10). Labeler built. **Pilot not started: needs the owner.** |
| 4. Attempt detection | ⚪ waits on labels |
| 5. Finish prediction + science | ⚪ design frozen (PREREG); Phase 5/6 options memo in `docs/DECISION_PHASE5_6.md` |
| 6. Overlay | 🟡 renderer + red/blue corner preview with pose scores (`tools/overlay/`, `tools/preview/`) |
| 7. Expansion | ⚪ |

## Open
- 🔴 Pilot labeling (owner; short sittings, see `HUMAN_TASKS.md`).
- 🔴 Kaggle account + phone verification (owner), which unlocks the pose fine-tune.
- 🟡 Corners: recommended fight data + one click per clip. Glove color alone is unreliable (UFC gloves are mostly black).
- 🟡 Remaining referee errors (~10%) and frames where the second fighter is never detected.

## Where to read more
`docs/CODE_TOUR.md` (how the code fits together) · `docs/BRIEF.md` (latest brief) · `HUMAN_TASKS.md` (owner to-dos) · `research/referee/*/RESULTS.md` · `research/pose_sweep/FINDINGS.md`
