# RNCV brief (2026-10-19)

🟢 done · 🟡 in progress · 🔴 needs you · ⚪ not started. Times are estimates. You asked to park human tasks for later, so nothing below is urgent tonight and no notification is sent.

## 🔴 Decisions waiting on you
1. **Corner (red/blue) labeling:** (a) one click per clip in the UI, or (b) pull red/blue from fight data and match by appearance. Main session will recommend one.
2. **May helper sessions commit to git?** CLAUDE.md says main only. Recommended: keep main-only (fewer conflicts) unless it becomes a bottleneck.
3. **Phase 5/6 option:** [memo](DECISION_PHASE5_6.md). Recommended: 5-B + 6-A.

## 🔴 Your tasks (top 3, full list in [HUMAN_TASKS.md](../HUMAN_TASKS.md))
1. **Pilot labeling in short sittings:** 3–5 attempts, 15–20 min each, with `tools/labeler/index.html` ([PILOT.md](../phase3_labels/PILOT.md): 8 successes + 7 failures).
2. **Read [CODE_TOUR.md](CODE_TOUR.md)** (30 min).
3. **Corner decision** (above).

## What changed since last brief
- 🟢 PREREG frozen (b8d817d). `gh` installed and signed in. 3 clips saved. Red/blue previews watched and looked good.
- 🟢 Pose sweep on UFC clips done; the score threshold was the culprit and pose_smoke was re-tuned (score 0.3 / nms 0.65) with two-fighter tracking. See `reports/pose_smoke.md` for numbers.
- 🟢 Code tour written.

## What the agents are doing
- 🟡 **ref-appearance, ref-detector:** working on the referee fix (so the referee isn't mistaken for a fighter).
- 🟢 Idle, safe to archive: chief-of-staff, critic, entrepreneur, ufc-labels, code-tour, build-phase2.
- ⚪ Not started: the 150-attempt labeling, Kaggle pose run, Phases 4–7.
