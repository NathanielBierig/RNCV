# labels.csv quality check

Rows: **51** · fights: **29** · outcomes: tap 22, escape 13, position_change 10, unconscious 5, bell 1 · found_via: finish_list 42, candidate_round 9
Label time per attempt (minutes): median **1.4**, total 99 (from `label_min` in notes).
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
| 37 (0f51869f, R3, 95.2-118.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 38 (0f51869f, R3, 123.1-130.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 39 (0f51869f, R3, 136.5-144.8 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 40 (3eea92e7, R4, 173.2-182.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 41 (d69bd8e5, R2, 86.5-87.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 42 (d69bd8e5, R2, 94.0-105.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 43 (d69bd8e5, R2, 188.6-191.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 44 (68fe62ba, R4, 162.8-165.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 45 (034c04e4, R3, 168.5-177.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 46 (8bc0c220, R1, 202.8-248.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 47 (2ba11e0b, R3, 227.5-243.2 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 48 (2ba11e0b, R3, 254.1-264.5 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 49 (9124740f, R1, 266.8-276.5 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 50 (7990b671, R3, 31.0-37.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 51 (0730c4e6, R2, 123.1-129.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
