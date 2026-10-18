# RNCV brief (2026-10-18, first brief)

🟢 done · 🟡 in progress · 🔴 needs you · ⚪ not started. Times are estimates.

## 🔴 Decisions waiting on you

1. **Approve the pre-registration** → [research/rnc_science/PREREG.md](../research/rnc_science/PREREG.md) (10 min).
   - What it is: 3 yes/no predictions written *before* looking at results (H1 arm under chin → more finishes; H2 body triangle/hooks → more finishes; H3 defender's two-hands-on-one-arm → fewer finishes).
   - **Recommended: approve.** It's what makes the science credible. Say "approve PREREG" or what to change.
   - Honest note: with ~150 attempts only big effects (≥25-point difference in finish rate) are reliably detected; small ones will come out "inconclusive".
2. **Phase 5/6 option choice** → memo not written yet ([docs/DECISION_PHASE5_6.md](DECISION_PHASE5_6.md), ⚪ pending). Nothing to do until it exists; I'll flag it here.

## 🔴 Your tasks (top 3, most urgent first)

Full list: [HUMAN_TASKS.md](../HUMAN_TASKS.md)

1. **Ask a training partner to be second rater** (5 min). Longest lead time. Message is in HUMAN_TASKS.
2. **Approve PREREG** (10 min), see above.
3. **Save 3 UFC RNC clips locally** (20 min) → `data\clips\`, links in [HUMAN_TASKS.md](../HUMAN_TASKS.md). This tests the biggest technical risk: does pose tracking survive tangled cage footage?

## What changed since last brief
- 🟢 Footage decision: **UFC only** ([FOOTAGE.md](FOOTAGE.md)).
- 🟢 RNC style tags added (figure-four, palm-to-palm, gable, wrist-pull, short choke, one-arm).
- 🟢 Phase 2 baseline finished ([reports/TRAINING_STATUS.md](../reports/TRAINING_STATUS.md)): macro-F1 **0.46** (guessing the most common class: 0.14). Works: standing 0.92, turtle 0.73–0.81, back 0.59–0.65. Fails: half guard (0.05/0.08) and "who is on top" pairs. Likely it finds the position but swaps the roles (hypothesis, not yet tested). Scores are optimistic: same athletes in train and test.
- 🟢 Pre-registration draft v0.1 written. 🟢 Eval harness hardened (11 tests pass).
- 🔴 Behind/at risk: the labeling tool (`tools/labeler/`) doesn't exist yet, so the 15-attempt pilot can't start. PREREG approval comes first anyway.

## What the agents are doing
- 🟡 **chief-of-staff**: plan, critique fixes, coordination. Working.
- 🟡 **build-phase2**: VICOS classifier (next: save predictions, merge roles, role-invariant features; MLP not run). Working.
- 🟡 **ufc-labels**: RNC candidate list (677 finishes, 3,330 fighter-rounds). Working.
- 🟡 **entrepreneur**: business angles (20 ideas, shortlist of 5). Working.
- 🟢 **critic**: 22 issues found, fixes applied. Idle.
- ⚪ Not started: pilot labeling, Kaggle pose run, Phases 4–7.
