# Pre-registration: what makes a UFC rear-naked choke finish? (FROZEN v1.0)

> v1.0 (2026-10-19): v0.2 approved by the user and frozen, with one added exclusion rule (§3, atypical chokes). No pilot outcome had been tabulated.
>
> v0.2 (2026-10-18), from user review: hand-picked sampling with per-fighter caps (§2); bell excluded from the primary analysis (§3); the exploratory factor list expanded and multi-tag styles added (§6). Still a draft, so these changes are not amendments.

**Status: FROZEN v1.0** (approved by the user 2026-10-19). Committed *before* any pilot outcome is tabulated. The commit hash is cited in the write-up, proving the hypotheses came before the data. Later changes are allowed only as dated amendments at the bottom, never silent edits.

## 1. Question
Among UFC RNC attempts, which technical states at a fixed early moment are associated with the attempt finishing?

## 2. Data
- **Population:** UFC fights 2018–2026 with at least one RNC attempt.
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
`rnc_style_at_L` (key contrast: figure_four vs wrist_pull), `rnc_style_sequence` (descriptive), `back_context`, `forearm_placement`, `choking_hand_tucked`, `second_hand_on_traps`, `squeeze_direction`, `chin_tucked`, `opponent_flattened`, round, weight class, `attacker_side` (sanity check: should be null). More may be added after the user's technique research, but only before v1.0 is frozen. Exploratory results are hints for a future study, never claims.

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
_(none yet)_
