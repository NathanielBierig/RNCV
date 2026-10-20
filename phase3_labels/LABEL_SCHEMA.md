# RNC attempt labeling schema (Phase 3)

One row per **attempt** in `labels.csv`. Labels are derived data only (timestamps and categories); no video is stored in the repo.

## Columns

| column | type | rule |
|---|---|---|
| `fight_id` | str | ufcstats fight id (last path segment of the fight URL). Must exist in `rnc_successes.csv` or `failed_attempt_candidates.csv` |
| `round` | int | 1-5 |
| `attempt_start_s` | float | Seconds from the **start of the round** on the round clock (see "Clock" below), 0.1 s precision |
| `attempt_end_s` | float | Same clock. Must be > `attempt_start_s` |
| `attacker` | str | Fighter applying the choke, name exactly as in the CSVs |
| `defender` | str | Other fighter |
| `sub_type` | str | `rnc` for this phase. Use `other_choke` / `not_a_choke` only to explain a candidate that turned out not to be an RNC; those rows are kept for audit but excluded from training |
| `outcome` | enum | `tap`, `ref_stop`, `unconscious`, `escape`, `position_change`, `bell` |
| `success` | bool | `True` iff outcome in {`tap`, `ref_stop`, `unconscious`}. Derived; keep it filled so the file is self-checking |
| `camera_cut_flag` | enum | `none`, `cut_in` (a cut/replay interrupts the attempt but the clock continues), `cut_out` (part of the attempt is not shown). Rows with `cut_out` are excluded from the clean evaluation set |
| `notes` | str | Free text: grip details, video id, "replay shown", doubts. **Reserved tokens:** `pilot` (one of the first 15 attempts), `no_clock` / `clock=finish_anchor` (set by the labeler: round times blank, or derived from the known finish time instead of the on-screen clock), `compilation` (clip from a compilation/highlight video whose on-screen clock is unreliable: QA skips round-time checks and the analysis treats `attempt_start_s`, `attempt_end_s` and `fight_time_s` as missing; durations from `video_time_*` stay valid) |

Optional helper columns that make review faster (not required by the model code): `video_url`, `video_time_start`, `video_time_end` (position in the video file, for the reviewer's own use, not the round clock), `reviewer`, `confidence` (1-3).

## Optional "science" fields (reviewer-labeled)

Added for the study of which details predict a finish. All are **reviewer-labeled from video**, optional, and may be blank when not visible (blank is not the same as `unclear`). Definitions live in `research/rnc_science/FACTORS.md` (main session); if the two disagree, FACTORS.md wins.

| column | values | note |
|---|---|---|
| `choke_arm_position` | `under_chin`, `over_jaw`, `unclear` | where the choking arm sits when the lock is sought |
| `control` | `two_hooks`, `body_triangle`, `one_hook`, `none` | leg control at attempt start |
| `opponent_flattened` | bool | defender's back/chest flat on the mat |
| `defender_two_on_one` | bool | both defender hands on the choking arm |
| `rnc_style_at_L` | `figure_four`, `palm_to_palm`, `gable`, `wrist_pull`, `short_choke`, `one_arm`, `unclear` | ONE grip style at the landmark (start + 2 s). Definitions in FACTORS.md "RNC style tags"; `wrist_pull` = the "Dagestani" forearm/wrist grip with no figure-four |
| `rnc_style_sequence` | style tags joined by `>` | every style seen during the attempt, in order, e.g. `wrist_pull>figure_four` |
| `forearm_placement` | `blade`, `v_elbow`, `across_jaw`, `unclear` | at the landmark (FACTORS.md) |
| `choking_hand_tucked` | bool | at the landmark (definition being confirmed, FACTORS.md) |
| `second_hand_on_traps` | bool | at the landmark |
| `squeeze_direction` | `straight_back`, `tilt_choke_side`, `tilt_away`, `pull_up`, `unclear` | at the landmark |
| `chin_tucked` | bool | defender, at the landmark |
| `found_via` | `finish_list`, `candidate_round`, `random_fight` | how this attempt was found (PREREG §2) |
| `view_blocked` | bool (blank = no) | the landmark view was blocked (referee, camera cut, angle): all factor fields are blank because they could not be seen, not because they were "unclear". Set with **X** in the labeler. Analysis treats these rows as missing factors, never as a factor level |
| `state_changes` | `t:field=value` joined by `>`, e.g. `6.4:upper_body=body_lock>9.0:control=body_triangle` | changes after the landmark, logged with **G**; `t` = seconds since attempt start. Fields: control, upper_body (body_lock / seatbelt / none), choke_arm_position, forearm_placement, choking_hand_tucked, second_hand_on_traps, squeeze_direction, defender_two_on_one, chin_tucked, opponent_flattened, back_context, rnc_style. Only changed fields are stored (the G panel pre-selects the current state and saves the difference); the full state at any time = landmark values + changes so far. **Descriptive and secondary hazard model only, never primary predictors** (PREREG §4: no post-landmark or time-held predictors) |
| `back_context` | `ground_back`, `turtle_ride`, `standing_back`, `scramble` | where the back attack happens |
| `attacker_side` | `left`, `right` | which arm is the choking arm |
| `seconds_to_lock` | float | seconds from back control established to the choke going in |
| `round` | int | already a core column; repeated here only for the analysis table |
| `fight_time_s` | float | seconds since the fight began = (round - 1) x 300 + `attempt_start_s` (valid for 5-minute rounds; fill by script, not by hand) |

`round` and `fight_time_s` are not reviewer-labeled in practice: `round` is core and `fight_time_s` is derived from it and `attempt_start_s`.

## Definitions

**Start of attempt** = the first frame where *all* hold:
1. attacker has **back control** (hooks in, or body triangle, or standing/clinch back control with both arms around the torso), and
2. the attacker's choking arm is **across the neck**, under the chin or over the jaw, and the second hand is working to lock it (hand on the opposite biceps/shoulder, or gripping the wrist).

A hand fight, seat-belt control with no arm across the neck, or "searching for the neck" is **not** yet an attempt. Mark the start at the moment the arm is across the neck and the lock is being sought, not at the first back take.

**Gotcha: re-starts.** If the defender strips the arm and the attacker reinstates it later (new clear arm-across-neck state), that is a **new attempt row** unless the gap is under 2 s with no loss of back control, in which case it is one attempt.

**End of attempt** = the earliest of:
- `tap`: verbal or physical tap (the end is the frame of the tap)
- `ref_stop`: referee waves it off or steps in (defender goes limp but conscious, or ref judges no intelligent defense)
- `unconscious`: defender goes unconscious (end = time of first full limp frame)
- `escape`: defender gets out, i.e. the choking arm is no longer across the neck and the attacker has lost back control, or the defender clearly turns into the attacker/faces him
- `position_change`: attacker abandons the choke (transitions to mount, armbar, etc.) or the defender reverses to top while the choke is stopped
- `bell`: round ends while the choke is still on

**Outcome priority** when several apply: `unconscious` > `tap` > `ref_stop` > `bell` > `escape` > `position_change`.

**Success** is a property of the attempt, not of the fight. If the attacker chokes someone in round 1 and loses a decision in round 3 the round-1 attempt is still `success=False` (if it failed).

## Clock

Use the on-screen round clock. The broadcast clock counts down from 5:00, so convert with `attempt_s = 300 - clock_remaining_s`. ufcstats finish times are elapsed time in the round (a finish at 2:46 is 166 s). For finishes the ufcstats finish time (`finish_time_in_round_s` in `rnc_successes.csv`) is the anchor: the `tap`/`ref_stop`/`unconscious` end time should be within about 3 s of it. A bigger gap means a data or clock problem to resolve in `notes`.

## Rules

1. **Camera cut** (broadcast switches to the crowd or replay and back): keep one attempt row, set `camera_cut_flag`, and pick times from the round clock.
2. **Replays** are never labeled as separate attempts.
3. **Round-level evidence** from `failed_attempt_candidates.csv`: it lists fighter-rounds with UFC-scored submission attempts of any type, not only RNC. Most candidates will not contain an RNC. A candidate round watched in full with no RNC is a real negative for the "attempt detector": set its queue `status` to `watched_no_rnc` (not a labels.csv row). QA counts these.
4. **Ambiguous** (unsure it was a real choke): do not guess. Put the row in `labels_ambiguous.csv` with the same columns plus `why`.
5. **Back control without a choke attempt** for 10+ s is not a row here; Phase 2 (back-control detector) handles that class.
6. Two reviewers on a random 10% subset; report agreement (start/end within 1 s, same outcome).

## Review priority

Check in this order; stop when about **150 attempts** are labeled (target split: about 60 successes from `rnc_successes.csv`, about 90 failed attempts):

1. **Recent fights first (2022 to 2026).** Better video quality (HD, 60 fps), consistent graphics and clock.
2. **Free or easy to view:** UFC's official free YouTube channel and UFC Fight Pass previews; prefer fights with full-fight or extended highlight videos you can view legally.
3. **Rounds with `sub_att_count >= 2`** in the candidates file are the most likely to hold a real, long attempt.
4. **Winner-attacker rounds** (`attacker_won_fight = True`) in early rounds, then lost-fight attackers.
5. Start with the successes (finish time known, easiest to align), then the candidates.

Skip 1994 to 2004 fights unless nothing else is available (SD video, odd rules, unreliable clock).

## Example row

```csv
fight_id,round,attempt_start_s,attempt_end_s,attacker,defender,sub_type,outcome,success,camera_cut_flag,notes
7db1a3dac7e343e7,5,<your_start>,166.0,Brendan Allen,Christian Leroy Duncan,rnc,<tap|ref_stop|unconscious>,True,none,"end anchored to ufcstats finish 2:46 = 166 s"
```

(Placeholders in `<>`: only the finish time comes from ufcstats; start time and outcome type come from video review.)
