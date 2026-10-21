# Pose pipeline: fresh-eye review on real UFC RNC frames (2026-10-21)

## One-screen summary
- 🔴 **Correct pair, by eye: 1–4 of 48 frames for every pipeline.** "Both fighters tracked" (94% median in reports/pose_attempts_combined.md) measures only that two skeletons exist. At the 48 eval frames C had two tracked slots in 37 frames, and both were the right people in 4.
- 🔴 **The main failure is mixed skeletons, not the referee.** At least one kept skeleton spans both fighters (or is junk) in 39–42 of 48 frames. The referee was kept in 4–6 of 48.
- 🔴 **Root cause of the mixing is the detector.** In the hard frames, *no* raw candidate from any model sits cleanly on the choker: RTMO-m, v1, v1 with looser NMS (0.9), or v2. select() and the tracker can't pick a skeleton that was never proposed. Mixing is not caused by the NMS cutoff, and v2 is not better than v1.
- 🟢 **Referee filter bug found and fixed (prototype D):** `referee_score` *ignores* too-dark pixels, but a black shirt is mostly too-dark pixels. So the referee is judged on his bare forearm and highlights, and scores 0.2–0.3 ("fighter"). Counting a dark pixel as half "not skin": AUC 0.92 → **0.99** on the old 79-referee eval set. On the new frames, referee kept 6 → 3 of 48, and crowd or black-bar junk kept as a fighter about 5 → 1. Patch: `referee_dark.patch`.
- 🟡 **27 of 48 frames are hard even for a human:** 13 are close-ups through the cage, plus cage-side, wide, low-res and occluded shots. Only 23 of 48 are clean views. Even on those, the best pipeline gets both fighters right in 3 of 23.
- **Next step:** stop tuning selection. Either test a close-contact pose model on this eval, or change what the overlay needs (see the ranked fixes below).

## The eval (Task 1)
- 48 frames = 3 per labeled attempt (start + 2 s, middle, end − 1 s; row 12 is 0.4 s long, so it uses 25/50/90% of the window). Each pipeline runs its real `select()` + `TwoSlotTracker` over the 1 s before the frame (stride 2), so fills behave as in production.
- A = RTMO-m 0.3/0.65. B = rncv_pose_v1.onnx 0.25. C = B + RTMO fallback (`pose_attempts.detect`). D = C + dark-aware referee score (thr 0.6). E = D + no fill when the stale pose now looks like a referee.
- Graded by eye from small renders (`data/pose_review/sheets/rowNN.jpg`, local only). Columns are in `eval.csv`. "OK" means the person's head, shoulders and most visible joints are right. I graded strictly: a skeleton with one fighter's head on the other's legs counts as mixed. A 3-frame full-res spot check confirmed the mixed calls. One grader and small images, so treat each count as ±2.

| Pipeline | Defender OK | Choker OK | **Both OK** | Referee kept | Junk/mixed kept | Both OK, clean views only (n=23) |
|---|---|---|---|---|---|---|
| A RTMO-m | 7 | 4 | **1** | 5 | 39 | 0 |
| B fine-tuned v1 | 9 | 5 | **3** | 4 | 42 | 3 |
| C v1 + RTMO fallback (current) | 10 | 7 | **4** | 6 | 40 | 3 |
| D = C + dark-aware referee | 11 | 7 | **4** | 3 | 40 | 3 |
| E = D + no referee fill | 11 | 7 | **4** | 2 | 40 | 3 |

## Root causes (Task 2)
1. **Mixed or merged skeletons: 39–42 of 48.** One-stage models (RTMO, YOLO-pose) predict one box per person, then that box's joints. In back control the two bodies share almost the same box, so the model outputs one skeleton that borrows joints from both, or two near-copies of it. This was confirmed on all 6 hard frames in `data/pose_review/raw_candidates.jpg` (every raw candidate, 4 detector settings). The v1 fine-tune (Harmony4D + VICOS, 4 h) did not fix it, and neither did v2. The earlier referee/detector RESULTS.md already said "RTMO merges the tangled pair into one". That was the real problem all along, not the referee.
2. **Referee kept: 4–6 of 48.** There are three separate reasons:
   - **Dark pixels ignored** (fixed by D). Row 5 start: the referee's torso is 84% too-dark pixels, and the lit 16% are 84% "skin", so his score is 0.22. Why the old eval (58% → 10%) didn't show it: it was scored on RTMO skeletons from 3 whole clips with referees mostly standing in the light. Attempt frames have the referee crouching close in shadow, and C mostly uses v1 skeletons. Dark skin is **not** the cause. Fighters' torsos are 6–15% too-dark (median per clip, 15% in the Sterling clip) vs 56–87% for referees. At threshold 0.6, D flags 0 of 152 fighters on the old set.
   - **Referee merged into a fighter skeleton** (row 5 mid: 0.54 even with D; row 7 end: 0.59). No pixel rule fixes a skeleton that is half referee.
   - **Tracker fills a stale referee pose** for up to 0.5 s after the filter drops him (rows 1, 2, 6). E removes this, but it changed only 1 frame.
3. **Unknown means kept.** `referee_score` returns 0.5 when nothing is visible, and the rule drops only scores > 0.5. So skeletons in the black pillarbox bars and crowd members pass (rows 10, 13, 16). D fixes this as a side effect: dark bars now score high.
4. **Junk filter → 0 kept (row 13).** `implausible()` correctly drops the cage-net skeleton, but nothing else was proposed. This is the detection problem again, not a filter bug.
5. **Camera:** 13 of 48 frames are close-ups through the cage, where no model (and barely a human) can tell the bodies apart.

## Fixes ranked by expected impact vs. effort (Task 3)
| # | Fix | Effort | Measured / expected gain |
|---|---|---|---|
| 1 | **Apply `referee_dark.patch`** (dark pixels count 0.5 as "not skin"; REF_THR 0.6) | 5 min | Measured: referee kept 6 → 3 of 48, crowd/bar junk ≈ 5 → 1, old-set AUC 0.92 → 0.99, 0 fighters flagged at 0.6. One new referee keep (row 7 end, 0.59, just under 0.6). |
| 2 | **Report correctness, not existence:** keep `eval.csv` as the gate and re-grade after any model change; drop "both tracked" as the headline | 1 h per re-grade | No accuracy gain, but stops false 🟢s. |
| 3 | **Test a close-contact model on this eval before more pipeline work.** Top-down on two separate person boxes still needs a box detector that splits the pair (fight-judge doesn't). Candidates: Harmony4D's own fine-tuned top-down model, BUCTD, or a longer v1 fine-tune on Harmony4D grappling with full-res crops | days, Kaggle GPU | Unknown. This is the only lever on the 40/48 mixed frames. Pass bar: ≥ 50% both-OK on the 23 clean frames. |
| 4 | **Reframe the overlay:** pool all joints and assign RNC roles (defender head/neck, wrists/elbows near it) instead of needing two whole skeletons; or a pair-crop classifier trained on the labeled attempts | 1–3 days | Unknown, but it sidesteps the per-person split that fails here. `rnc_low` already leans this way. |
| 5 | E (no referee fill) | 10 min | 1 frame (3 → 2 referee kept). Optional. |

Prototypes: `proto_fix.py` (`pipe_D`, `no_ref_fill`) and `ref_dark.py` (old-set check). Re-score with `render.py --extra proto_fix:pipe_D`.

## What NOT to bother with
- More `select()` rules (overlap pair, proximity, role-specific low joint bar, junk ratios): they choose among candidates, and the right candidate usually isn't there.
- Looser NMS (0.9) or the v2 model: more candidates, all near-copies of the same mixed skeleton.
- Track-level referee voting: referee errors are now 2–3 of 48. The mixed skeletons are the problem.
- Tuning the referee threshold on these 48 frames: too few referee cases (0.55 vs 0.6 changes 1 frame). Keep 0.6, which was chosen on the old set.
- Temporal smoothing: it smooths a wrong skeleton.

## Files
`cache.py` (raw model outputs → `data/pose_review/cache.pkl`), `common.py` (replays pipelines A/B/C), `render.py` (grading sheets), `eval.csv` (grades), `raw_candidates.py` (is the right skeleton ever proposed?), `ref_dark.py`, `proto_fix.py`, `referee_dark.patch` (for src/, applies cleanly with `git apply`).
