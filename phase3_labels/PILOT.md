# Labeling queues and first session (PREREG v0.2 section 2)

**Retired:** `pilot_15_RETIRED.csv` (the seeded random-fight draw, `draw_pilot.py`) is kept only as a record. It is not a subset of `random_10.csv` and full-fight watching at random was judged too slow. Do not use it for labeling.

Everything below is rebuilt by `.venv/Scripts/python -I build_queues.py`. Frame for the random draw: fights from 2018 on in `rnc_successes.csv` or `failed_attempt_candidates.csv` (1,273 fights).

## Files

| file | rows | `found_via` | what to do |
|---|---|---|---|
| `labeling_queue_successes.csv` | 315 | `finish_list` | Valid RNC finishes 2018+, recent first. Jump to `jump_to_elapsed_s` (finish minus 60 s, in elapsed-round seconds) or the `jump_to_clock_remaining` on the broadcast clock (assumes a 5:00 round). Label every RNC attempt from there to the end of the round, including earlier failed attempts if the 60 s window shows one |
| `labeling_queue_failures.csv` | 47 | `candidate_round` | Rounds with `sub_att_count >= 2` where the attacker already had at least one RNC win before the event (as-of priors from `fighter_priors.csv`). Watch that round only. The attempt type is unknown, so "no RNC in this round" is a valid result: log it |
| `random_10.csv` | 10 | `random_fight` | 10 fights drawn uniformly at random, seed `20261019`. Watch the full fight and label every RNC attempt. Exempt from caps, never trimmed. These fights are removed from the two queues |

Caps: at most 3 attempts per attacker and 3 per defender, counted jointly (successes fill their slots first, then failures). Overturned/DQ and "technical submission" finishes are not in the success queue (they stay in `rnc_successes.csv`).

## First labeling session: 8 successes + 7 failures

- **Successes:** queue ranks 1 to 8 (`session = 1`): the 8 most recent finishes (Aug to Oct 2026).
- **Failures:** queue ranks 1 to 7 (`session = 1`).
- The random 10 are a separate job, not part of this session.

Notes for the session: every row has `ufc_youtube_channel_search` (a search scoped to the official `@UFC` channel) and `fight_pass_lookup`. There are no direct video links, because search hits often turn out to be game footage or re-uploads. `free_full_fight_on_ufc_youtube` starts as `unverified`. Set `status` to `unwatchable` if you can't legally reach a live-feed copy after a 10-minute lookup, and take the next row in the same queue. Never skip a row because it looks hard. Record the skip count.

## Caveats (read before analysing)

- **The failure queue is small (47) and selective.** Requiring a prior RNC win, `sub_att >= 2` and the caps leaves few rounds. Its failures come from fighters known for RNCs, so failure rates from it are not base rates. Only `random_10` gives a base rate.
- **`random_10` will hold few attempts.** The frame is mostly candidate-only fights and about 1 in 3 candidate rows contains an RNC (unverified), so expect about 5 attempts in 10 fights. If that is too few for a base rate, extend the same seeded draw to 20 fights (change the count in `build_queues.py`; the first 10 would change, so decide before watching).
- Recent-first ordering puts the first session entirely in 2025 to 2026; later years will be needed for variety.
