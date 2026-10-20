# Pre-registration: what makes a UFC rear-naked choke finish? (FROZEN v1.0)

> v1.0 (2026-10-19): v0.2 approved by the user and frozen, with one added exclusion rule (§3, atypical chokes). No pilot outcome had been tabulated.
>
> v0.2 (2026-10-18), from user review: hand-picked sampling with per-fighter caps (§2); bell excluded from the primary analysis (§3); the exploratory factor list expanded and multi-tag styles added (§6). Still a draft, so these changes are not amendments.

**Status: FROZEN v1.0** (approved by the user 2026-10-19). Committed *before* any pilot outcome is tabulated. The commit hash is cited in the write-up, proving the hypotheses came before the data. Later changes are allowed only as dated amendments at the bottom, never silent edits.

## 1. Question
Among UFC RNC attempts, which technical states at a fixed early moment are associated with the attempt finishing?

## 2. Data
- **Population:** UFC fights 2018–2026 with at least one RNC attempt. *(Amended A1, 2026-10-19: men's divisions only; see §9.)*
- **Sampling (hybrid; watching full fights at random is too slow):**
  - **Successes:** chosen from the 677-finish list (the finish time is known, so jump straight to it). Choosing by outcome keeps the factor comparisons (odds ratios) valid; it only distorts the *overall* finish %, which comes from the random subset below.
  - **Failures:** from rounds that UFC stats flag with submission attempts, and later from back-control moments flagged by the pose pre-labeler. No full-fight watching.
  - **Every** RNC attempt in a watched round is labeled, including failed attempts before a finish in the same round.
  - **Per-fighter cap:** at most 3 attempts per attacker and 3 per defender, so no single fighter (e.g. Charles Oliveira) dominates the results.
  - **Random subset:** about 10 fights drawn at random (fixed seed, list fixed before watching) and fully labeled. This gives the honest base finish rate.
  - Each row records `found_via` (`finish_list`, `candidate_round`, `random_fight`). The analysis adjusts for it.
- **Unit:** one attempt, per [LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md).
- **Target:** about 150 attempts, roughly balanced between successes and failures (balance from the hand-picked lists; the random subset is never trimmed).
- **Source:** live feed only (no replays), per [docs/FOOTAGE.md](../../docs/FOOTAGE.md).

## 3. Outcome
- `success` = tap, ref stoppage or unconscious.
- `escape` / `position_change` = failure.
- `bell` = **censored**: excluded from the primary logistic model, included as censored in the hazard model.
- **Atypical chokes** (e.g. one-armed or chin-linked chokes, as in Silva vs Delgado, Sep 2026) are tagged `rnc_style_at_L = one_arm`. They're **excluded from the primary model** but still counted and reported separately (count and finish rate).

## 4. Landmark and blinding
- Factors are coded at **L = 2 s after attempt start**. Eligible attempts are still ongoing at start + L + 2 s. Attempts that end sooner are reported separately (count and finish rate).
- **Blind coding:** the labeling tool pauses at start + L. Factors are coded there, *then* the clip plays on and the outcome is coded.
- No "deepest point", no "ever reached", no time-held predictor.

## 5. Hypotheses (confirmatory; primary model, at most 4 df)

| # | Factor (at L) | Coding | Prediction |
|---|---|---|---|
| H1 | `arm` | under_chin vs not | Higher odds of a finish |
| H2 | `lower_body` | body_triangle or two hooks vs less | Higher odds of a finish |
| H3 | `defender_two_on_one` | yes vs no | Lower odds of a finish |
| — | `round_time_left` | seconds at start | Adjustment only (bell censoring); no hypothesis |

## 6. Exploratory (labeled as such in every output)
`rnc_style_at_L` (key contrast: figure_four vs wrist_pull), `rnc_style_sequence` (descriptive), `upper_body` (added A2), `back_context`, `forearm_placement`, `choking_hand_tucked`, `second_hand_on_traps`, `squeeze_direction`, `chin_tucked`, `opponent_flattened`, round, weight class, `attacker_side` (sanity check: should be null). More may be added after the user's technique research, but only before v1.0 is frozen. Exploratory results are hints for a future study, never claims.

## 7. Analysis
- **Primary:** Firth logistic regression, profile-likelihood 95% CIs, reported as odds ratios.
- **Sensitivity checks:** (a) cluster bootstrap by attacker; (b) `unclear` coded as each extreme; (c) excluding attempts with `camera_cut_flag = cut_out`.
- **Secondary:** discrete-time hazard model (1-s bins; finish vs escape as competing outcomes; bell censored).
- **Reliability:** a second rater codes at least 30 attempts; Cohen's κ per factor. A factor with κ < 0.4 is reported as "not reliably codable from broadcast", whatever its OR.

## 8. Decision rules (written before data)
- A hypothesis is **supported** if its 95% CI excludes OR = 1 in the predicted direction; **contradicted** if it excludes 1 in the opposite direction; otherwise **inconclusive**. Inconclusive is a valid result and is reported as such.
- No factor is added to the primary model after seeing outcomes.
- Power (two groups of about 75, alpha = 0.05): about 90% for a 25-point difference in finish rate, about 50% for 15 points, about 25% for 10 points. Small effects are expected to come out inconclusive.

## 9. Amendments

### A1 (2026-10-19): population restricted to men's divisions
- **Change:** §2 Population becomes "UFC **men's** fights 2018–2026 with at least one RNC attempt". Fights whose `weight_class` contains "Women's" are out of scope for every analysis (primary, exploratory and base rate).
- **Why:** the owner decided to study men's divisions only. Women's and men's RNC finishing may differ (body size, grip strength, division depth), and with about 150 attempts the study can't power a sex-by-factor comparison. Mixing them would add unexplained variation instead.
- **Timing:** made before any attempt was saved (`phase3_labels/labels.csv` did not exist yet) and before any pilot outcome was tabulated. No hypothesis, coding, model or decision rule changes.
- **Sampling consequences:**
  - The success and failure queues: women's rows are skipped at labeling time and recorded as `status = out_of_scope_womens` (not `unwatchable`). The per-fighter caps are unchanged.
  - `random_10.csv`: women's fights in the fixed draw are excluded and **not replaced**, so the draw stays exactly as fixed before watching. The base finish rate is computed from the remaining men's fights, and the write-up reports how many were excluded.
- **Limitation (stated in the write-up):** findings apply to men's UFC divisions only.

### A2 (2026-10-20): upper-body control variable and a timestamped change log
- **Change 1, new exploratory variable:** `upper_body` ∈ {`body_lock`, `seatbelt`, `none`}, the attacker's upper-body control. It is separate from `control` (leg control), so the primary factor `lower_body` (§5, H2) is **unchanged**. It is added to §6 as exploratory only.
- **Change 2, change log:** after the landmark, changes in `control`, `upper_body`, `choke_arm_position`, `defender_two_on_one`, `chin_tucked`, `opponent_flattened`, `back_context` and `rnc_style` are recorded with their time since attempt start (`state_changes`, LABEL_SCHEMA.md).
- **Use rule:** `state_changes` and any post-landmark value are **descriptive, or time-varying covariates in the secondary discrete-time hazard model (§7) only. Never primary-model predictors.** This restates §4: longer attempts have more time to change state and more time to end in a finish, so post-landmark states would leak the outcome into the primary model.
- **Why:** labeling showed that attempts evolve, e.g. a body lock is added mid-attempt. Recording this makes the hazard model's "current state" bins possible and gives the write-up a descriptive picture of how chokes develop.
- **Timing:** made before any attempt was saved (`phase3_labels/labels.csv` had 0 rows). No hypothesis, primary coding, model or decision rule changes.
- **A2 addendum (2026-10-20, same day, owner request):** the change log also covers `forearm_placement`, `choking_hand_tucked`, `second_hand_on_traps` and `squeeze_direction` (all existing exploratory landmark fields). Same use rule: descriptive / secondary hazard model only.
