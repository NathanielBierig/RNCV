# RNCV progress (as of 2026-10-18)

🟢 done · 🟡 in progress · 🔴 blocker / needs your decision · ⚪ not started

## Done
- 🟢 **Phase 1, resource search:** datasets, models and repos compared with their licenses. Stack: YOLO11-pose / RTMO, FightersMMA detector data, VICOS positions.
- 🟢 **Direction chosen:** #1 Science-based RNC (which details make a choke finish) + #2 live overlay demo.
- 🟢 **Plan + directions:** `docs/PLAN.md`, `docs/DIRECTIONS.md`.
- 🟢 **RNC candidate list:** 677 UFC RNC finishes (452 since 2015) with round and time, plus 3,330 fighter-rounds with unfinished attempts (`phase3_labels/`).
- 🟢 **Label schema + study design:** `phase3_labels/LABEL_SCHEMA.md`, `research/rnc_science/FACTORS.md` (with a power check: ~150 attempts detect only big effects).
- 🟢 **Overlay renderer:** works on a synthetic clip (`tools/overlay/`).
- 🟢 **Eval harness:** fight splits, time horizons, event matching (`tools/eval_harness/`).
- 🟢 **Venture ideas:** 20 ideas, shortlist of 5 (`research/venture/`).
- 🟢 **Repo:** dedicated git repo, committed piece by piece.

## In progress
- 🟡 **Phase 2 VICOS classifier:** pipeline written. Training was still running at shutdown; re-run `src/train_baseline.py`.
- 🟡 **Critique:** 22 issues found (`research/critique/CRITIQUE.md`).

## Blockers (from the critique; need your decision)
- 🔴 **Footage access:** no $0 legal way to get UFC frames for pose extraction. Pick: (i) local-only copies at your own ToS risk, CPU pose, never upload to Kaggle; or (ii) your own gym footage for the CV + UFC for hand labeling only.
- 🔴 **VICOS "Back" exists in only one sequence:** its score can't validate RNC detection. Gate on hand-tagged UFC frames instead.
- 🟡 **Fix before labeling:** merge the two label schemas into one, sample by fight (not by outcome), treat the bell as censored rather than a failure, compute fighter stats as of fight date, split test by fighter graph / hash.

- 🟡 **Align `research/rnc_science/FACTORS.md` with PLAN §5a/5b** (the critic's science review): fixed-landmark design, no time-held predictor, at most 4 primary factors, Firth CIs, blind factor coding, a second rater. Then write `PREREG.md`.
- 🟢 Eval harness hardened per the critique (11 tests pass).

## Next
- ⚪ Decide on footage access → freeze the label schema → pilot-label 15 RNC attempts with a stopwatch.
- ⚪ Run the Kaggle pose notebook (`notebooks/kaggle_yolo_pose_vicos.ipynb`).
- ⚪ Phases 4–7: attempt detection → success prediction → overlay on real clips → more submissions.
