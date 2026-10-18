# RNC Labeler

This is one offline HTML file. There's no server, nothing is installed and nothing is uploaded: the video stays on your laptop. It writes `labels.csv` rows in exactly the [LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md) format, using the codes from [FACTORS.md](../../research/rnc_science/FACTORS.md).

**Open:** double-click `tools/labeler/index.html` in Chrome or Edge. Firefox works too, but can't write the CSV file directly.

## Set up once per session
1. **Load fight list(s) CSV**: pick `phase3_labels/rnc_successes.csv` and/or `failed_attempt_candidates.csv`. The Fight dropdown then fills in fight_id, round, attacker and defender. For finishes it also shows the UFC stats finish time as an anchor.
2. **Link labels.csv file** (Chrome/Edge): pick `phase3_labels/labels.csv`, which is created if missing. Every save is written straight into it, and rows already in the file are kept. In other browsers, use **Download labels.csv** when you're done. Rows are also kept in the browser between visits.
3. **Open video**: a private local clip of one attempt, ~10 s before the start up to the end.

## Label one attempt (target: under 4 min)
| Step | Key |
|---|---|
| Pause on a frame where the round clock is visible and type the time **remaining** (e.g. `3:12`). The tool converts it to elapsed time (300 − remaining) for every timestamp. Re-sync after replays or clock stoppages. | <kbd>C</kbd> |
| Find the start (back control + arm across the neck + second hand locking, per LABEL_SCHEMA) and press start. | <kbd>S</kbd> |
| The video **plays to start + 2 s and freezes**. The factor panel opens; you can scrub back but not forward. Code what you see (**blind**: you haven't seen the ending). | <kbd>1</kbd>–<kbd>9</kbd> per field, then <kbd>Enter</kbd> |
| Play on and press end at the tap, stoppage, limp, escape, position change or bell. | <kbd>Space</kbd>, then <kbd>E</kbd> |
| Outcome panel: outcome, camera_cut_flag, sub_type, confidence; optional seconds_to_lock and notes. | <kbd>1</kbd>–<kbd>9</kbd>, then <kbd>Enter</kbd> |

**Other keys:** <kbd>Space</kbd> play/pause · <kbd>←</kbd>/<kbd>→</kbd> ±1 s (<kbd>Shift</kbd> ±5 s) · <kbd>,</kbd>/<kbd>.</kbd> ±1 frame · <kbd>[</kbd>/<kbd>]</kbd> speed · <kbd>B</kbd> back 10 s · <kbd>U</kbd> undo last row · <kbd>↑</kbd>/<kbd>↓</kbd> change field in a panel · <kbd>Esc</kbd> cancel · <kbd>Ctrl</kbd>+<kbd>Enter</kbd> confirm while typing notes.

## What it fills automatically
- `success` (from the outcome)
- `fight_time_s` = (round − 1) × 300 + start
- `video_url` / `video_time_start` / `video_time_end` (the clip's file name and position, for your own re-checks)
- `reviewer`
- `label_min=…` appended to `notes`, for the pilot's timing measurement (untick the box to stop)

**Warning:** if a finish's end is more than 3 s from the UFC stats finish time, it warns you. That usually means the clock sync is off.

## Back-control hints (optional)
**Back-control hints CSV** loads a file with `start_s,end_s` columns in **video seconds**. They show as green bars on the timeline; click one to jump there. The build session can export this from `data/pose/<clip>.npz` once pose runs on your clips. The tool doesn't read `.npz` directly, because there isn't a fixed `.npz` format yet.

## Known limits
- The frame step assumes 30 fps.
- Rounds are assumed to be 5 minutes.
- Can't write the file directly outside Chrome/Edge.
- Tested on a synthetic 12-s WebM in Chromium: landmark pause, forward-lock, clock math, CSV quoting and the anchor warning all work. **Not yet timed on a real UFC clip**, so the 4-minute target is untested until your pilot.
