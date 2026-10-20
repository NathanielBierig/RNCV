# RNC Labeler

This is one offline HTML file. There's no server, nothing is installed and nothing is uploaded: the video stays on your laptop. It writes `labels.csv` rows in exactly the [LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md) format, using the codes from [FACTORS.md](../../research/rnc_science/FACTORS.md).

**Open:** double-click `tools/labeler/index.html` in Chrome or Edge. Firefox works too, but can't write the CSV file directly.

## Set up once per session
1. **Load fight list(s) CSV**: select `phase3_labels/labeling_queue_successes.csv`, `labeling_queue_failures.csv` and `random_10.csv` together. The raw `rnc_successes.csv` / `failed_attempt_candidates.csv` also work. The Fight dropdown lists them in queue order and fills in fight_id, round, attacker, defender and **found_via** (PREREG §2). For finishes it also shows the UFC stats finish time as an anchor, plus the queue's "jump to" time. If the other fighter is the one choking, press <kbd>W</kbd> or ⇄ to swap the names.
2. **Link labels.csv file** (Chrome/Edge): pick `phase3_labels/labels.csv`, which is created if missing. Every save is written straight into it, and rows already in the file are kept. In other browsers, use **Download labels.csv** when you're done. Rows are also kept in the browser between visits.
3. **Open video**: a private local clip of one attempt, ~10 s before the start up to the end.

## Label one attempt (target: under 4 min)
| Step | Key |
|---|---|
| Pause on a frame where the round clock is visible and type the time **remaining** (e.g. `3:12`). The tool converts it to elapsed time (300 − remaining) for every timestamp. Re-sync after replays or clock stoppages. | <kbd>C</kbd> |
| Find the start (back control + arm across the neck + second hand locking, per LABEL_SCHEMA) and press start. | <kbd>S</kbd> |
| The video **plays to start + 2 s and freezes**. The factor panel opens with **all 12 landmark fields**: arm position, forearm placement, style at L, choking hand tucked, second hand on traps, squeeze direction, leg control, two-on-one, chin tucked, flattened, back context, attacker side. You can scrub back but not forward. Code what you see (**blind**: you haven't seen the ending). Blank = not visible. | <kbd>1</kbd>–<kbd>9</kbd> per field, then <kbd>Enter</kbd> |
| Play on. Each time the grip changes, add it to the **style sequence**, which starts with the style at L; repeats are skipped. | <kbd>T</kbd> then <kbd>1</kbd>–<kbd>7</kbd> |
| Press end at the tap, stoppage, limp, escape, position change or bell. **Bell keeps its own code**; the analysis treats it as censored. | <kbd>Space</kbd>, then <kbd>E</kbd> |
| Outcome panel: outcome, camera_cut_flag, sub_type, confidence; editable style sequence (`a>b>c`, checked against the allowed tags); optional seconds_to_lock and notes. | <kbd>1</kbd>–<kbd>9</kbd>, then <kbd>Enter</kbd> |

**Other keys:** <kbd>W</kbd> swap attacker/defender · <kbd>Space</kbd> play/pause · <kbd>←</kbd>/<kbd>→</kbd> ±1 s (<kbd>Shift</kbd> ±5 s) · <kbd>,</kbd>/<kbd>.</kbd> ±1 frame · <kbd>[</kbd>/<kbd>]</kbd> speed · <kbd>B</kbd> back 10 s · <kbd>U</kbd> undo last row · <kbd>↑</kbd>/<kbd>↓</kbd> change field in a panel · <kbd>Esc</kbd> cancel · <kbd>Ctrl</kbd>+<kbd>Enter</kbd> confirm while typing notes.

**View blocked:** if the referee, a camera cut or the angle hides the choke at the 2 s pause, press <kbd>X</kbd> in the factor panel. Every factor is left blank in one go and the attempt gets `view_blocked=True`, so you skip the 12 fields. During an attempt, <kbd>X</kbd> toggles the flag on or off.
**State changes (G):** when something changes after the 2 s landmark (body lock added, hooks in or out, arm slides under the chin, two-on-one starts or ends, chin untucks, defender flattened), press <kbd>G</kbd>. The video pauses and every field is shown with its **current value highlighted** (the 2 s value, updated by earlier G entries; `blank` if it had none). Press a number only where something changed (<kbd>0</kbd> = back to the current value), then Enter. Only real changes are stored. Grip style is in the panel too (it also extends the style sequence). Each change is saved with its time since the attempt start in `state_changes`. These are descriptive only: the main analysis uses the landmark values.
**No clock on screen? Skip C.** For a fight with a known finish (from the queue), just label. When you save the finishing attempt, the clock is **anchored to the known finish time** (the end of the tap = the official finish), and any earlier attempts from the same clip and round are back-filled. Rows saved before an anchor exists get `no_clock` in notes and blank round times; their durations from the video times stay valid. Pressing **C** on a visible clock still works and takes priority. The choking side (left or right) can now be changed in **G** too.

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
- Tested on synthetic 12-s WebMs in Chromium with the real queue files. These all work: landmark pause, forward-lock, all 12 landmark fields, the style sequence, found_via from the queue, clock math, CSV quoting, the anchor check, and the column order matching LABEL_SCHEMA. **Not yet timed on a real UFC clip**, so the 4-minute target is untested until your pilot.
