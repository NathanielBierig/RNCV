# RNCV roadmap (updated 2026-10-29)

All times are estimates. "Sitting" = about 20–30 min of labeling.

**MVP 0.1 =** one command takes a UFC clip and outputs an overlay video: **"RNC attempt" detected automatically**, a box on the fighters, the main visible factors, and a **finish-probability bar from a model trained on your labels**. It's for private demo, not public.

| Milestone | Where it stands | Result / status | Next |
|---|---|---|---|
| ✅ M0 Foundations | Plan, PREREG + amendments A1–A4, labeler, QA, queues, overlay renderer | done | — |
| 🟡 **M1 Attempt detector usable** | 40 labeled fights, ~65 min of no-choke footage | frame ROC-AUC **~0.75** (target 0.80 not met); finds back attacks but not the start second; fails on highlight reels; camera-angle fixes gave no gain | more fights; mirrored training once ~20 new clips exist (only 5 of 41 feature clips still have video, so old clips can't be backfilled) |
| 🔴 M2 First factor detector | pilot on whole-image features: near chance (best κ 0.24, bar 0.4) | neck-crop model being built from saved crops (16 fights) | decision at ~150 attempts |
| 🟡 M3 Science v1 | **75 attempts / 43 fights**; second rater not yet | pilot report + exploratory findings done; confirmatory test waits on the recomputed target | footage supply is the bottleneck |
| 🟢 M4 Finish-probability model | model v0.8 (expert priors + labels), held-out Brier 0.244 vs 0.256 at 2 s, 0.223 vs 0.256 as the position changes | done for the pilot; improves with labels | — |
| 🟢 **MVP 0.3** | side-tab overlay, locked reticle, skeleton flashes, HP with seconds of air, local test app | done; polish for the pilot release | — |
| ⏸️ Parked | Precise skeletons (pose merges tangled fighters; 4/48 correct). Revisit with a different kind of pose model later | — | — |

## Main focus (owner, 2026-11-01): the computer labels on its own and gives the odds and the time to a finish
Where each step stands, on fights left out of training:

| Step | Status | Evidence |
|---|---|---|
| Find the back attack | 🟡 works on full broadcasts | frame ROC-AUC ~0.75, 95% of attempts caught, ~0.5 false alarms/min |
| Place the start second | 🔴 | correct start ~9% |
| Read arm, grip, legs, hand fight | 🔴 near chance | best κ 0.24 (bar 0.4), [factor_pilot.md](../reports/factor_pilot.md) |
| Odds from pixels alone | 🔴 no gain | Brier 0.256 vs 0.257 for guessing the average, even with labeled start times, [auto_odds.md](../reports/auto_odds.md) |
| Odds from public stats alone | 🔴 no gain end to end | Brier 0.248 vs 0.256 with the true attacker, but 0.258 vs 0.259 in the [full pipeline](../reports/auto_demo.md) |
| Pick the attacker | 🟢 works | 96% from control time in the round |
| Time to a finish | 🔴 no gain | 23 s error from the detector's start, 3.3 s even with the true start (3.4 s for guessing the median); finishes are roughly flat after 5 s ([time_curve.md](../reports/time_curve.md)) |

Plan, in order (estimates):
1. 🟢 **Keep labeled videos on the laptop** (owner, 2026-11-01; `cleanup_clips.py` now only lists). Only 5 of 41 feature clips still have video, and every better model needs the pixels. Old clips can be re-downloaded from `phase3_labels/downloads_log.csv`.
2. **Log more moments.** Each G-panel change gives extra training frames for the same labeling work.
3. **Start with the detail that shows a hint:** the two-on-one (κ 0.24 with DINOv2 at 20 fights, below the 0.4 bar). Legs fell back to chance.
4. **Stronger image model on the laptop CPU** (no GPU; Kaggle stays closed to footage). DINOv2 at 20 fights of crops: best κ 0.24, others near 0. Retry at about 30 fights.
5. 🟡 **Crude automatic demo built** (`tools/mvp/auto_demo.py`, local only): flags the attack and picks the attacker, but its odds are a coin flip. The round number is still given by hand.

## Pilot release: portfolio-ready (owner, 2026-10-29)
Goal: proof that it works, basic findings and a working model, presented honestly as a pilot. No waiting for 150 attempts. Estimate: 1–2 weeks of sessions, mostly Main's work. Labeling continues on the side.

| # | Piece | What it shows | Status |
|---|---|---|---|
| 1 | **Footage-free demo video** | Proof it works. The tracking layer (boxes, neck reticle, skeleton flashes) drawn on black from derived keypoints, plus the side tab, so no UFC pixels | 🟢 `--no-pixels`, README GIF, [30-second reel](media/rncv_reel.mp4) |
| 2 | **Interactive model explorer** (public page, no video) | Model function. Pick the arm, grip, legs and hand fight, watch the finish chance and HP over a simulated choke. Runs from `model.json` in the browser | 🟢 `docs/explorer/` (also a claude.ai page) |
| 3 | **Pilot findings** | README charts + [pilot report](paper/PILOT_REPORT.md) + back exposures | 🟢 drafted |
| 4 | **Local app** (`tools/app`) | The real detector on a clip you drop in (works on full broadcasts, not highlight reels) | 🟢 |
| 5 | **Outward README** | 30-second story, honest limits, one-command app | 🟢 |
| 6 | **Public hygiene** | `tools/make_public.py` exports a clean copy (224 files, 0 issues, fresh history); license still to choose | 🟡 |

## Public release (owner, 2026-10-26: "when the project is more promising, soon")
The GitHub repo becomes outward-facing:
1. **README for outsiders:** what RNCV is, results, demo GIF/video, no local-machine details (local paths already removed from public docs; `CLAUDE.md`, `HUMAN_TASKS.md` and the internal docs move out or get cleaned before going public).
2. **"Test the detector" portal:** an interactive app (drop a clip → overlay with finish % + consciousness gauge). Hosted demo or a local one-command app; never redistributes UFC footage.
3. **Research paper (thesis style) on choke variables:** the pre-registered study ("what makes the UFC RNC finish"), methods, results with confidence intervals, the evidence review, limitations. PDF in the repo.
4. **Checklist before flipping to public:** licenses (VICOS NC, AGPL YOLO), no UFC pixels in the repo or history, no personal paths or tokens, reproducible commands.

**The critical path is footage and labels** (2026-10-29): official uploads are nearly used up, and failure rounds are scarce. The pilot release doesn't wait on them.
