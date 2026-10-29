# RNCV roadmap (updated 2026-10-29)

All times are estimates. "Sitting" = about 20–30 min of labeling.

**MVP 0.1 =** one command takes a UFC clip and outputs an overlay video: **"RNC attempt" detected automatically**, a box on the fighters, the main visible factors, and a **finish-probability bar from a model trained on your labels**. It's for private demo, not public.

| Milestone | Where it stands | Result / status | Next |
|---|---|---|---|
| ✅ M0 Foundations | Plan, PREREG + amendments A1–A4, labeler, QA, queues, overlay renderer | done | — |
| 🟡 **M1 Attempt detector usable** | 40 labeled fights, ~65 min of no-choke footage | frame ROC-AUC **~0.75** (target 0.80 not met); finds back attacks but not the start second; fails on highlight reels; camera-angle fixes gave no gain | more fights; orientation-aware (mirrored) training |
| 🔴 M2 First factor detector | pilot on whole-image features: near chance (κ ≤ 0.17) | neck-crop model being built from saved crops (15 fights) | decision at ~150 attempts |
| 🟡 M3 Science v1 | **74 attempts / 43 fights**; second rater not yet | pilot report + exploratory findings done; confirmatory test waits on the recomputed target | footage supply is the bottleneck |
| 🟢 M4 Finish-probability model | model v0.8 (expert priors + labels), held-out Brier 0.245 vs 0.254 at 2 s, 0.224 vs 0.254 as the position changes | done for the pilot; improves with labels | — |
| 🟢 **MVP 0.3** | side-tab overlay, locked reticle, skeleton flashes, HP with seconds of air, local test app | done; polish for the pilot release | — |
| ⏸️ Parked | Precise skeletons (pose merges tangled fighters; 4/48 correct). Revisit with a different kind of pose model later | — | — |

## Pilot release: portfolio-ready (owner, 2026-10-29)
Goal: proof that it works, basic findings and a working model, presented honestly as a pilot. No waiting for 150 attempts. Estimate: 1–2 weeks of sessions, mostly Main's work. Labeling continues on the side.

| # | Piece | What it shows | Status |
|---|---|---|---|
| 1 | **Footage-free demo video** | Proof it works. The tracking layer (boxes, neck reticle, skeleton flashes) drawn on black from derived keypoints, plus the side tab, so no UFC pixels | 🟢 `--no-pixels`, README GIF |
| 2 | **Interactive model explorer** (public page, no video) | Model function. Pick the arm, grip, legs and hand fight, watch the finish chance and HP over a simulated choke. Runs from `model.json` in the browser | ⚪ |
| 3 | **Pilot findings** | README charts + [pilot report](paper/PILOT_REPORT.md) + back exposures | 🟢 drafted |
| 4 | **Local app** (`tools/app`) | The real detector on a clip you drop in (works on full broadcasts, not highlight reels) | 🟢 |
| 5 | **Outward README** | 30-second story, honest limits, one-command app | 🟡 |
| 6 | **Public hygiene** | Move CLAUDE.md / HUMAN_TASKS / internal docs out, license, `tools/release_check.py` clean | ⚪ |

## Public release (owner, 2026-10-26: "when the project is more promising, soon")
The GitHub repo becomes outward-facing:
1. **README for outsiders:** what RNCV is, results, demo GIF/video, no local-machine details (local paths already removed from public docs; `CLAUDE.md`, `HUMAN_TASKS.md` and the internal docs move out or get cleaned before going public).
2. **"Test the detector" portal:** an interactive app (drop a clip → overlay with finish % + consciousness gauge). Hosted demo or a local one-command app; never redistributes UFC footage.
3. **Research paper (thesis style) on choke variables:** the pre-registered study ("what makes the UFC RNC finish"), methods, results with confidence intervals, the evidence review, limitations. PDF in the repo.
4. **Checklist before flipping to public:** licenses (VICOS NC, AGPL YOLO), no UFC pixels in the repo or history, no personal paths or tokens, reproducible commands.

**The critical path is footage and labels** (2026-10-29): official uploads are nearly used up, and failure rounds are scarce. The pilot release doesn't wait on them.
