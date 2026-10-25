# RNCV: instructions for Claude sessions

RNCV = RNC + CV. A UFC-only study of what makes rear-naked chokes finish (pre-registered science) plus a live finish-probability overlay. The owner knows BJJ but isn't an ML expert. Budget $0; laptop has no GPU; Kaggle for GPU (never with UFC footage).

## Start here (read these instead of asking for history)
1. `PROGRESS.md`: overall status (color-coded).
2. `docs/BRIEF.md`: latest brief + pending decisions. `docs/DECISIONS.md`: decisions made.
3. `HUMAN_TASKS.md`: the owner's to-do list, most urgent first.
4. Then only what the task needs: `docs/PLAN.md` (phases), `research/rnc_science/PREREG.md` + `FACTORS.md` (science + code book), `phase3_labels/LABEL_SCHEMA.md`, `docs/FOOTAGE.md`.

## Rules
- **Git:** commit piece by piece with clear messages (`Phase N: ...`, `Docs: ...`, `Tools: ...`, `Research: ...`), then push to `origin main` (github.com/NathanielBierig/RNCV, private). Background helper sessions never commit; the main session does.
- **Footage:** UFC video never goes into git, Kaggle, cloud or social media. Only derived data (keypoints, timestamps, labels) is kept. Clips live in `data/clips/` (git-ignored).
- **Science:** PREREG.md is frozen at v1.0 before pilot labeling; after that, only dated amendments. FACTORS.md is the single code book.
- **Python:** OpenCV/rtmlib need a short-path venv (`C:\Users\netan\.venvs\ufc-cv`) because of a Windows long-path DLL issue.
- **Communication:** short, color-coded bullets (🟢 done, 🟡 in progress, 🔴 needs owner, ⚪ not started), terms defined on first use, estimates marked as estimates, honest about weak results. End with the owner's next action in bold. Batch the owner's to-dos into one notification.
- **Venvs (short paths):** `C:\Users\netan\.venvs\rncv` (pose, training), `ufc-cv` (OpenCV, pandas, Pillow, Kaggle CLI, QA, MVP demo), `clip` (open_clip image features).
- **Status (2026-10-25):** pose skeletons are unreliable in tangled positions (4/48 correct, `research/pose_review/REVIEW.md`); the no-pose attempt detector is at ROC-AUC ~0.70 (needs more fights); the MVP 0.1 demo's finish-% math was **rejected by the owner** (a time ramp crushed it: a locked choke read ~2%, a knockout ~30%). The finish model is being redesigned (`docs/MODEL_SPEC.md`, expert session) before more MVP UI work.
- **Background work:** start sessions or scheduled tasks only when the owner asks (they often do: "make an agent", "keep running"). Within a granted window, move on to the next issue instead of stopping to report. Don't burn tokens.
