# labels.csv quality check

Rows: **7** · fights: **3** · outcomes: tap 3, position_change 2, escape 1, unconscious 1 · found_via: finish_list 7
Label time per attempt (minutes): median **2.1**, total 24 (from `label_min` in notes).

🔴 fix before analysis · 🟡 check · ⚪ info

| Row | | Issue |
|---|---|---|
| 1 (d85c76a6, R2, 113.4-140.9 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 1 (d85c76a6, R2, 113.4-140.9 s) | 🔴 | overlaps row 2 (112.3-119.4 s vs 113.4-140.9 s), same fight + round; keep one, or make them consecutive attempts |
| 2 (d85c76a6, R2, 112.3-119.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 3 (d85c76a6, R2, 130.9-140.7 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 3 (d85c76a6, R2, 130.9-140.7 s) | 🔴 | overlaps row 1 (113.4-140.9 s vs 130.9-140.7 s), same fight + round; keep one, or make them consecutive attempts |
| 4 (c03b6b6c, R1, 275.7-293.1 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 5 (c03b6b6c, R1, 313.2-323.0 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 5 (c03b6b6c, R1, 313.2-323.0 s) | 🔴 | round time 313.2-323.0 s is outside 0-300 s; if the source is a compilation, add `compilation` to notes |
| 6 (c03b6b6c, R1, 325.6-337.3 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |
| 6 (c03b6b6c, R1, 325.6-337.3 s) | 🔴 | round time 325.6-337.3 s is outside 0-300 s; if the source is a compilation, add `compilation` to notes |
| 6 (c03b6b6c, R1, 325.6-337.3 s) | 🟡 | end 337.3 s is +249.3 s from the ufcstats finish (88 s); check the clock sync (C) |
| 7 (f8fce67a, R3, 92.8-101.4 s) | ⚪ | no `pilot` tag in notes (first 15 attempts should have it) |

Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.
Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing.
