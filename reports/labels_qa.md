# labels.csv quality check

Rows: **12** · fights: **5** · outcomes: position_change 4, escape 3, tap 2, unconscious 2, bell 1 · found_via: finish_list 7, candidate_round 5
Label time per attempt (minutes): median **1.4**, total 33 (from `label_min` in notes).
Watched rounds with **0 RNC attempts** (real negatives, status `watched_no_rnc` in the queues): **1** (Paddy Pimblett vs Jordan Leavitt R1)

🔴 fix before analysis · 🟡 check · ⚪ info

🟢 No issues found.

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
