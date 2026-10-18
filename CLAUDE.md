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
- **Background work:** paused by the owner on 2026-10-18 (secretary check-in disabled). Don't start sessions or scheduled tasks unless asked.
