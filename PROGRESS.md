# RNCV progress (as of 2026-10-26)

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## ▶ Next session starts here (2026-10-25)
1. **Labels:** 36 attempts / 20 fights (main-card successes + failure rounds), QA clean. Fastest next fights: [phase3_labels/FINDABLE_TOP18.md](phase3_labels/FINDABLE_TOP18.md).
2. **MVP 0.1** (`tools/mvp/demo.py`, a replay overlay: finish % for the attacker, a health bar for the defender) was **rejected on the math**: the time ramp made a locked figure-four read ~2% and a knockout ~30%. **Redesign first:** a math/model expert session writes `docs/MODEL_SPEC.md` (expert priors + labels; the number = chance this attempt finishes given the current state; tap → ~100%). The owner is answering alignment questions in batches.
3. **Automatic detection:** pose is parked (4/48 frames correct, [research/pose_review/REVIEW.md](research/pose_review/REVIEW.md)); the no-pose attempt detector is at ROC-AUC 0.70 on 20 fights. Re-test at ~40 fights: `research/attempt_clf/attempt_clf.py --crop --refresh`.
4. **Position classifier (VICOS):** 0.63 macro-F1 on original keypoints, 0.47 on YOLO, 0.50 on RTMO keypoints.
5. PREREG: v1.0 + A1 (men only) + A2 (upper_body, change log) + A3/A4 (cap = 5 attacking rounds / 20 attempts per attacker).

## Fresh-eyes review (2026-10-26, concept and user-facing)
- 🟢 Done: README rewritten for outsiders (results table with honest numbers); how-tos moved to [docs/OPERATIONS.md](docs/OPERATIONS.md); counts reconciled; MODEL_SPEC has a "current model" box; defender gauge renamed **choke meter** on screen ("consciousness" sounded like a medical measurement).
- 🔴 Owner decisions: (1) keep the name "choke meter"? (2) show **RESULT: TAP** instead of 100% at the tap? (3) a footage-free demo route for the public (label-driven stick-figure replay, own gym rolls with consent, or a private video for interviews only); (4) narrow the showcase to study + overlay, with the detector marked experimental.
- Reviewer's biggest risk: the public demo and app need UFC pixels, which can't be published. Plan B needed before going public.

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
| 2b. Pose on UFC | ⏸️ parked: fine-tunes v1/v2 done, but both fighters are correct in only 4/48 tangled frames. The overlay uses only confident parts. |
| 3. Labeling | 🟡 36 attempts / 20 fights, QA clean. Goal ~60 this week, ~150 for the study. ~1.5 min per attempt. |
| 4. Attempt detection | 🟡 experimental: frame ROC-AUC 0.70 on 20 fights, but a correct start on only ~6% of attempts; manual "attempt starts" key until M1 |
| 5. Finish prediction + science | 🟡 live model v0.6 (Brier 0.226 vs 0.270 base rate, gain not yet certain), v0.7 in progress; study waits on ~150 attempts |
| 6. Overlay | 🟡 replay demo (`tools/mvp/demo.py`): finish chance + choke meter + grip + tracking layer |
| 7. Expansion | ⚪ |

## Tools that exist
Labeler (S/E, blind 2-s panel, X blocked view, G state changes with the current value highlighted, clock anchored to the known finish, side panel, refuses queue files, re-reads the file before saving) · labels QA · pose-on-attempts report · red/blue preview · overlay renderer · eval harness · Kaggle CLI (token set).

## Where to read more
[README](README.md) (how-tos) · [CODE_TOUR](docs/CODE_TOUR.md) · [BRIEF](docs/BRIEF.md) · [HUMAN_TASKS](HUMAN_TASKS.md) · [research/referee/](research/referee/) · [research/pose_sweep/FINDINGS.md](research/pose_sweep/FINDINGS.md)
