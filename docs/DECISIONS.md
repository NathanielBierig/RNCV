# Decision log

Newest last. Owned by the secretary session.

## Made
| Date | Decision | Why |
|---|---|---|
| 2026-10-18 | Direction = science-based RNC study (which details predict a finish) + live finish-probability overlay as the showcase | Gives a credible result plus a demo; fits $0 budget and a laptop |
| 2026-10-18 | Footage: UFC only, no gym or other promotions ([FOOTAGE.md](FOOTAGE.md)) | Elite defense isolates technique from skill gap. Label from legal streams; private local clips for pose, never uploaded |
| 2026-10-18 | Added RNC style tags (figure_four, palm_to_palm, gable, wrist_pull, short_choke, one_arm) and `back_context` | The BJJ-relevant question is which grip/style finishes, not just whether a choke happens |
| 2026-10-18 | Repo = RNCV (dedicated git repo) | Keeps history clean and shareable as a portfolio piece |
| 2026-10-18 | Phase 2 eval = time-block folds, not leave-one-sequence-out | Each VICOS sequence drills only 2–4 positions; per-video splits leak (synced cameras) |
| 2026-10-19 | User approved PREREG v0.2 (to be frozen as v1.0 by the main session). Atypical chokes (e.g. one-armed) are to be tagged and kept out of the main model; rule to be added before freeze | Fixes the exclusion before any outcome is seen |

## Pending
| Decision | Status | My recommendation |
|---|---|---|
| Freeze PREREG v1.0 (commit) | 🟡 approved by user 2026-10-19, waiting on main session | Commit with the atypical-choke rule |
| Phase 5/6 option choice | ⚪ memo coming at `docs/DECISION_PHASE5_6.md` | Decide after reading the memo |
| Men's fights only? (pilot is men only so far) | 🔴 needs your call; needs a dated PREREG amendment before main labeling | Decide before the 150-attempt labeling; state it in the write-up |
| Mid-attempt change log (body lock, hooks, arm switch) in labeler + how to treat it statistically | 🟢 shipped by Main (af79470), press G | Log changes with timestamps as exploratory/time-varying only; keep primary model at the L=2 s landmark (avoids the 'longer attempts succeed more' bias) |
| PREREG amendment A2: new variable `upper_body` (body_lock / seatbelt / none), descriptive and secondary-hazard only | 🔴 needs your approval (Main is asking you) | Approve: it is added before any real labeling, and it is not a primary predictor |
