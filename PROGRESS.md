# RNCV progress (as of 2026-10-27)

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## ▶ Next session starts here (2026-10-28)
- **Labels: 73 attempts / 42 fights**, QA clean. 64 come from finish-list fights and only 9 from failure rounds: **failure rounds are the labeling priority** (5 fights on disk: [NEXT_SESSION.md](phase3_labels/NEXT_SESSION.md)). Official YouTube uploads are nearly used up; the owner can paste links.
- **Detector:** frame ROC-AUC **~0.75** on 40 fights (0.80 on 29 was partly luck). Finds back attacks; start timing and false alarms (~0.7–1.0/min) are the weak spots.
- **Finish model v0.8** (leaner v0.7c): Brier 0.245 vs 0.254 at 2 s (within noise); 0.224 vs 0.254 as the position changes. Six variants tested and logged ([MODEL_SPEC §4g](docs/MODEL_SPEC.md)).
- **Findings (exploratory):** [reports/findings_pilot.md](reports/findings_pilot.md). Hidden hand 75% vs 48% finished, flattened 66% vs 49%, finishes took a median 9.6 s on the neck (9.0 s in the published MMA data). Body triangle shows no edge per attempt, likely because leg control buys re-attacks, which this model doesn't count.
- **Factor recognition (M2):** not yet. Neck-crop pipeline running (15 fights so far); a decision at ~150 attempts.
- **MVP 0.3 demo:** side tab (detector, finish %, HP + seconds of air, factor boxes), calm skeleton flashes, locked reticle. README GIF updated.

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
| 4. Attempt detection | 🟡 experimental v2 ([report](reports/attempt_detector_v2.md)): frame ROC-AUC 0.74 (v1 0.70) on 19 fights, but a correct start on only ~8–22% of attempts; manual "attempt starts" key until M1 |
| 5. Finish prediction + science | 🟡 live model v0.6 (Brier 0.226) and v0.7c = v0.7 + coach priors (0.228; best over every second, 0.204); base rate 0.270. **v0.7c is the demo default (owner, 2026-10-26).** Study waits on ~150 attempts |
| 6. Overlay | 🟡 replay demo (`tools/mvp/demo.py`): finish chance + choke meter + grip + tracking layer |
| 7. Expansion | ⚪ |

## Tools that exist
Labeler (S/E, blind 2-s panel, X blocked view, G state changes with the current value highlighted, clock anchored to the known finish, side panel, refuses queue files, re-reads the file before saving) · labels QA · pose-on-attempts report · red/blue preview · overlay renderer · eval harness · Kaggle CLI (token set).

## Where to read more
[README](README.md) (how-tos) · [CODE_TOUR](docs/CODE_TOUR.md) · [BRIEF](docs/BRIEF.md) · [HUMAN_TASKS](HUMAN_TASKS.md) · [research/referee/](research/referee/) · [research/pose_sweep/FINDINGS.md](research/pose_sweep/FINDINGS.md)
