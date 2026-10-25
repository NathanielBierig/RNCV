# RNCV progress (as of 2026-10-25)

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## ▶ Next session starts here (2026-10-25)
1. **Labels:** 36 attempts / 20 fights (main-card successes + failure rounds), QA clean. Fastest next fights: [phase3_labels/FINDABLE_TOP18.md](phase3_labels/FINDABLE_TOP18.md).
2. **MVP 0.1** (`tools/mvp/demo.py`, a replay overlay: finish % for the attacker, a health bar for the defender) was **rejected on the math**: the time ramp made a locked figure-four read ~2% and a knockout ~30%. **Redesign first:** a math/model expert session writes `docs/MODEL_SPEC.md` (expert priors + labels; the number = chance this attempt finishes given the current state; tap → ~100%). The owner is answering alignment questions in batches.
3. **Automatic detection:** pose is parked (4/48 frames correct, [research/pose_review/REVIEW.md](research/pose_review/REVIEW.md)); the no-pose attempt detector is at ROC-AUC 0.70 on 20 fights. Re-test at ~40 fights: `research/attempt_clf/attempt_clf.py --crop --refresh`.
4. **Position classifier (VICOS):** 0.63 macro-F1 on original keypoints, 0.47 on YOLO, 0.50 on RTMO keypoints.
5. PREREG: v1.0 + A1 (men only) + A2 (upper_body, change log) + A3/A4 (cap = 5 attacking rounds / 20 attempts per attacker).

## Shelved (owner, 2026-10-21)
- **MVP (clip → pose → attempt detection → overlay with a danger bar):** wait for a more concrete model (needs ~100+ labeled attempts for a learned probability).
- **Design goal for the overlay/UI:** "gnarly and sciency, colorful but minimalistic". Owner wants **several design options first** (maybe with a design plugin), later.

## Decisions
- 🟢 Direction: science-based RNC + live overlay. UFC only, men's divisions only (A1). Clips local only.
- 🟢 PREREG v1.0 frozen (`b8d817d`) + A1 (men's only) + A2 (upper_body, change log = descriptive / hazard only).
- 🟢 Code book: [FACTORS.md](research/rnc_science/FACTORS.md); human guide: [LABELING_GUIDE.md](docs/LABELING_GUIDE.md) + [picture code book](docs/rnc_codebook.html).

## Phase status
| Phase | Status |
|---|---|
| 1. Resource search | 🟢 |
| 2. Position classifier (VICOS) | 🟢 GBM + swap aug 0.63 macro-F1 (original keypoints); 🟡 0.47 on YOLO11m keypoints (YOLO finds both athletes in only 46% of frames) |
| 2b. Pose on UFC | 🟡 RTMO-m + two-fighter tracker + skin/clothing referee filter. Labeled attempts: median 64% both-fighters coverage; finishes worst (33–46%). Fine-tune running on Kaggle. |
| 3. Labeling | 🟡 16 attempts / 6 fights (7 finish-list, 9 failure-round) + 1 watched negative round (Pimblett–Leavitt R1). Moreno–Royval R1 skipped (clip failed). QA clean. ~1.5 min per attempt. |
| 4. Attempt detection | ⚪ needs ~100+ labeled attempts |
| 5. Finish prediction + science | ⚪ design frozen; options memo [DECISION_PHASE5_6.md](docs/DECISION_PHASE5_6.md) |
| 6. Overlay | 🟡 renderer + red/blue preview tool |
| 7. Expansion | ⚪ |

## Tools that exist
Labeler (S/E, blind 2-s panel, X blocked view, G state changes with the current value highlighted, clock anchored to the known finish, side panel, refuses queue files, re-reads the file before saving) · labels QA · pose-on-attempts report · red/blue preview · overlay renderer · eval harness · Kaggle CLI (token set).

## Where to read more
[README](README.md) (how-tos) · [CODE_TOUR](docs/CODE_TOUR.md) · [BRIEF](docs/BRIEF.md) · [HUMAN_TASKS](HUMAN_TASKS.md) · [research/referee/](research/referee/) · [research/pose_sweep/FINDINGS.md](research/pose_sweep/FINDINGS.md)
