# labels.csv quality check

Rows: **16** · fights: **6** · outcomes: position_change 6, escape 5, tap 2, unconscious 2, bell 1 · found_via: candidate_round 9, finish_list 7
Label time per attempt (minutes): median **1.4**, total 41 (from `label_min` in notes).
Watched rounds with **0 RNC attempts** (real negatives, status `watched_no_rnc` in the queues): **1** (Paddy Pimblett vs Jordan Leavitt R1)

🔴 fix before analysis · 🟡 check · ⚪ info

| Row | | Issue |
|---|---|---|
| 16 (f030febe, R1, 249.1-258.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
