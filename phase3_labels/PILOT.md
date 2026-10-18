# 15-attempt pilot: fight draw (PREREG section 2)

`pilot_15.csv` is a seeded, year-stratified random draw of **fights** (not attempts), made before any video was watched.

- **Frame:** fights from 2018 on that appear in `rnc_successes.csv` or `failed_attempt_candidates.csv` (1,273 fights; 121 to 159 per year).
- **Seed:** `20261018` (numpy `default_rng`; frame sorted by `fight_id` before shuffling). Re-run `draw_pilot.py` to reproduce the file exactly.
- **Order:** shuffle within each year 2018 to 2026, then interleave the years round-robin, giving `global_order` 1 to 54. Rows 1 to 36 are `primary` (4 per year); rows 37 to 54 are `reserve` (2 per year).
- **Mix in the primary list:** 6 finish-list fights, 2 in both lists, 28 candidate-only. Candidate-only fights often have no RNC at all (about 1 in 3 hold one, unverified), so expect roughly 15 to 20 RNC attempts from the 36 primaries. That is a guess; the first fights will show the real rate.
- **`rounds_to_watch`:** every round in which ufcstats scored a submission attempt (candidate list), plus the finishing round for RNC finishes. Label **every** RNC attempt in those rounds, finish rounds included. `known_finish` is the ufcstats finish (round and time) for the RNC finishes; it anchors the clock (about ±3 s, see LABEL_SCHEMA.md).
- **Row field `found_via`** is `rnc_success`, `sub_att_candidate` or both; copy it to each attempt row.

## Stopping rule

Work through `global_order` strictly in order. Stop when **15 RNC attempts** are labeled (finish the fight you are in). Never stop on a success/failure quota and never skip around by interest. If a primary fight has no RNC attempt, that is a valid result: log it (0 attempts) so the hit rate is measured.

## Watch links: what is and is not in the file

There are **no direct video links**, deliberately. A search for the first fight returned a video-game simulation, and the other hits were third-party re-uploads; there is no way to confirm an official upload without opening each one. Each row has instead:

- `ufc_youtube_channel_search`: a search link scoped to UFC's official channel (`@UFC`), with both fighter names.
- `fight_pass_lookup`: the event name to search on UFC Fight Pass.
- `free_full_fight_on_ufc_youtube`: `unverified` for every row. Set it to `yes` or `no` after you look, and paste the official URL into `notes` if `yes`. I expect few of the 2023 to 2026 fights to be free.

## Substitution rule (no cherry-picking)

A fight counts as unwatchable only if you cannot reach a **legitimate, full, live-feed** copy (UFC Fight Pass, the official UFC channel, or a PPV/ESPN+ account you hold) after a 10-minute lookup. Then:

1. Replace it with the lowest-`global_order` unused `reserve` fight **from the same year**; if that year has none left, take the next unused reserve in global order.
2. Write the replaced fight's `fight_id` in `substituted_for` on the substitute's row, and set the replaced row's `status` to `unwatchable`.
3. Never substitute because a fight looks boring, hard, or has no obvious choke. Never pick a fight after seeing its video or highlights.
4. Report the substitution count in the write-up. If more than a third of the primaries need replacing, the sample is no longer random: say so.

`status` values: `todo`, `done`, `unwatchable`, `no_rnc_found`.
