# labels.csv quality check

Rows: **38** · fights: **20** · outcomes: tap 14, escape 11, position_change 8, unconscious 4, bell 1 · found_via: finish_list 29, candidate_round 9
Label time per attempt (minutes): median **1.2**, total 74 (from `label_min` in notes).
Watched rounds with **0 RNC attempts** (real negatives, status `watched_no_rnc` in the queues): **1** (Paddy Pimblett vs Jordan Leavitt R1)

🔴 fix before analysis · 🟡 check · ⚪ info

| Row | | Issue |
|---|---|---|
| 16 (f030febe, R1, 249.1-258.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 17 (755202fc, R1, 213.6-223.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 18 (b22eab3a, R3, 31.4-38.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 19 (b22eab3a, R3, 39.8-59.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 20 (652a956a, R2, 104.7-108.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 21 (652a956a, R2, 120.2-125.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 21 (652a956a, R2, 120.2-125.3 s) | 🟡 | end 125.3 s is +49.3 s from the ufcstats finish (76 s); check the clock sync (C) |
| 22 (01a4827b, R3, 104.7-108.8 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 23 (01a4827b, R3, 120.2-125.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 24 (7d4e49d8, R1, 166.0-173.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 25 (7d4e49d8, R1, 190.8-200.7 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 26 (6c44af21, R4, 209.6-218.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 27 (7d4c160d, R4, 147.5-156.8 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 28 (fd49f89b, R5, 260.4-270.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 29 (4f9939af, R4, 88.4-91.5 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 30 (4f9939af, R4, 145.3-156.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 31 (e9700d51, R2, 126.0-132.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 32 (79865287, R2, 143.4-167.6 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 33 (83084647, R3, 94.2-113.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 34 (919fb76d, R2, 171.6-179.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 35 (4dc5039b, R1, 65.8-79.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 36 (4dc5039b, R1, 81.3-94.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 37 (4dc5039b, R1, 104.6-126.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 38 (4dc5039b, R1, 274.5-286.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
