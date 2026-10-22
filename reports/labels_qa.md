# labels.csv quality check

Rows: **36** · fights: **19** · outcomes: tap 13, escape 10, position_change 8, unconscious 4, bell 1 · found_via: finish_list 27, candidate_round 9
Label time per attempt (minutes): median **1.2**, total 72 (from `label_min` in notes).
Watched rounds with **0 RNC attempts** (real negatives, status `watched_no_rnc` in the queues): **1** (Paddy Pimblett vs Jordan Leavitt R1)

🔴 fix before analysis · 🟡 check · ⚪ info

| Row | | Issue |
|---|---|---|
| 16 (f030febe, R1, 249.1-258.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 17 (755202fc, R1, 213.6-223.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 18 (b22eab3a, R3, 31.4-38.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 19 (b22eab3a, R3, 39.8-59.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 20 (01a4827b, R3, 104.7-108.8 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 21 (01a4827b, R3, 120.2-125.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 22 (7d4e49d8, R1, 166.0-173.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 23 (7d4e49d8, R1, 190.8-200.7 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 24 (6c44af21, R4, 209.6-218.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 25 (7d4c160d, R4, 147.5-156.8 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 26 (fd49f89b, R5, 260.4-270.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 27 (4f9939af, R4, 88.4-91.5 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 28 (4f9939af, R4, 145.3-156.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 29 (e9700d51, R2, 126.0-132.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 30 (79865287, R2, 143.4-167.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 31 (83084647, R3, 94.2-113.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 32 (919fb76d, R2, 171.6-179.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 33 (4dc5039b, R1, 65.8-79.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 34 (4dc5039b, R1, 81.3-94.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 35 (4dc5039b, R1, 104.6-126.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 36 (4dc5039b, R1, 274.5-286.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
