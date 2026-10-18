# Pre-registration: what makes a UFC rear-naked choke finish? (DRAFT v0.1)

**Status: DRAFT, awaiting user approval.** Once approved, it's committed as v1.0 *before* any pilot outcome is tabulated. The commit hash is cited in the write-up, proving the hypotheses came before the data. Later changes are allowed only as dated amendments at the bottom, never silent edits.

## 1. Question
Among UFC RNC attempts, which technical states at a fixed early moment are associated with the attempt finishing?

## 2. Data
- **Population:** UFC fights 2018–2026 with at least one RNC attempt.
- **Sampling frame (by fight, not by outcome):** fights drawn at random, stratified by year, from (RNC finishes ∪ rounds with submission attempts), with the list fixed *before* watching. **Every** RNC attempt in every watched round is labeled, finish rounds included. Each row records `found_via` (finish list or candidate list).
- **Unit:** one attempt, per [LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md).
- **Target:** about 150 attempts. Stopping rule: stop at 150 attempts or 60 fights, whichever comes first. Never stop on a success/failure quota.
- **Source:** live feed only (no replays), per [docs/FOOTAGE.md](../../docs/FOOTAGE.md).

## 3. Outcome
- `success` = tap, ref stoppage or unconscious.
- `escape` / `position_change` = failure.
- `bell` = **censored**: excluded from the primary logistic model, included as censored in the hazard model.

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
`rnc_style` (key contrast: figure_four vs wrist_pull), `back_context`, `opponent_flattened`, round, weight class, `attacker_side` (sanity check: should be null).

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
