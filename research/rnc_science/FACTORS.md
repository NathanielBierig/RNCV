# Science-based RNC: what makes a rear-naked choke finish?

Study design for direction #1, **UFC only** (see [docs/FOOTAGE.md](../../docs/FOOTAGE.md)). The analysis rules follow [PLAN.md §5a](../../docs/PLAN.md) (revised after the critic's science review). If this file and PLAN §5a disagree, PLAN wins until `PREREG.md` is written and committed.

## Unit of analysis

One **attempt** as defined in [LABEL_SCHEMA.md](../../phase3_labels/LABEL_SCHEMA.md). `success` = tap, ref stoppage or unconscious. `bell` = **censored** (not a failure).

**Landmark coding:** every factor is coded at **L = 2 s after the attempt start**, paused, *before* watching the ending (blind coding). No "deepest point" or "ever reached" codings, and no "time held" predictor: duration is a result of the outcome.

## Primary factors (at most 4 df; these are the pre-registered hypotheses)

| Factor | Coding | Hypothesis |
|---|---|---|
| `arm` | under_chin vs not | Under the chin finishes more often |
| `lower_body` | body_triangle or two hooks vs less | Stronger leg control finishes more often |
| `defender_two_on_one` | yes / no | Both defender hands on the choking arm lowers the finish rate |
| `round_time_left` | seconds | Adjusts for bell censoring (not a technique claim) |

## Secondary / exploratory factors (reported as exploratory)

| Factor | Coding | Question |
|---|---|---|
| `rnc_style_at_L` | one style tag (below), at the landmark | Does grip style change finish rate? E.g. figure-four vs the Dagestani wrist pull |
| `rnc_style_sequence` | all styles in order, `>`-joined, e.g. `wrist_pull>figure_four` | How attackers switch grips; do switches finish more often? (descriptive) |
| `forearm_placement` | `blade` (bony edge of the forearm across the throat) / `v_elbow` (elbow centered under the chin, biceps and forearm on the two sides of the neck) / `across_jaw` | Proposed definitions; refine after your research |
| `choking_hand_tucked` | yes / no: choking hand hidden deep (on the opposite biceps or shoulder) vs just gripping | **Definition to confirm** with your research |
| `second_hand_on_traps` | yes / no: second hand on the defender's trapezius or shoulder instead of behind the head | Common in short-choke / wrist-pull styles |
| `squeeze_direction` | `straight_back` / `tilt_choke_side` / `tilt_away` / `pull_up` | Proposed; probably hard to see on broadcast, so check κ |
| `chin_tucked` | yes / no (defender) | The defender's first line of defense |
| `back_context` | ground_back / turtle_ride / standing_back / scramble | Do chokes from rides and standing finish differently than from classic back mount? |
| `opponent_flattened` | yes / no | Flattened = can't turn in |
| `round`, weight class | stats | Fatigue and division effects |
| `attacker_side` | left / right | Sanity check: should show no effect |

Excluded as predictors (part of the escape definition, so tautological): `defender_turning`, `arm = off`.

## RNC style tags

RNCs are dynamic, so styles are coded twice: `rnc_style_at_L` is **one** tag at the landmark (this is what the statistics use: one value per attempt at a fixed moment), and `rnc_style_sequence` lists **every** style seen, in order (this tells the story of how the grip evolved). The exploratory factor list grows after the user's technique research; every addition is logged here with a date **before** PREREG v1.0 is frozen.

| Tag | What it looks like | Typical of |
|---|---|---|
| `figure_four` | Choking hand grips the opposite biceps, other hand behind the defender's head (classic mata leão) | BJJ-style back takes |
| `palm_to_palm` | Hands clasped palm to palm, choking forearm across the throat | Common when the head is defended |
| `gable` | Hands clasped thumbless (gable or S-grip) behind the neck | Wrestlers, scrambles |
| `wrist_pull` | Second hand grabs the choking arm's **wrist or forearm** and pulls it across; no hand behind the head, no figure-four | The "Dagestani" style, often from a ride or body lock (e.g. Khabib / Islam-style back attacks) |
| `short_choke` | Choking arm only partly across: hand ends at the attacker's own shoulder or the defender's far collar line, blade of the forearm on the throat, second hand pushes the elbow or head | Sneaky finish over the jaw / when a full lock is denied |
| `one_arm` | No second hand engaged; squeezing with one arm while the other controls the body or wrist | Transitional, scrambles |
| `unclear` | Grip not visible (angle, cut, gloves hidden) | Report the unclear rate per tag |

**Exploratory question:** do `wrist_pull` (Dagestani) attempts finish at a different rate than `figure_four`, adjusted for the primary factors? With about 150 attempts, only a large difference is detectable (see the power table). Treat any result as "suggestive" and a reason to collect more.

## Analysis (from PLAN §5a)

- **Firth logistic regression** (removes small-sample bias) with profile-likelihood 95% CIs. Sensitivity check: a cluster bootstrap by attacker.
- Descriptive finish rates per level with **Wilson 95% CIs**.
- Secondary: a discrete-time hazard model (1-s bins; finish vs escape as competing outcomes; bell = censored).
- **Second rater** (a training partner) on at least 30 attempts → Cohen's κ (agreement above chance; aim for > 0.6), reported per factor. Style tags are likely the hardest to agree on, so measure them.
- Associations, not causes. Wide CIs are a result. Exploratory findings are labeled exploratory.

## How much data? (estimates; two groups of 75, alpha = 0.05)

| True difference in finish rate | Example | Power |
|---|---|---|
| 25 points | 55% vs 30% | about 90% |
| 15 points | 45% vs 30% | about 50% |
| 10 points | 40% vs 30% | about 25% |

Style tags split the data into 6 groups, so per-tag counts are small: expect only the most common contrast (probably figure-four vs wrist_pull) to be estimable.

## Next

- Write and commit `PREREG.md` (hypotheses, codings, landmark, model, decision rules) **before** the 15-attempt pilot.
- Output: `analysis.ipynb` with tables and a forest plot, plus a public write-up using derived data only ("What actually finishes the RNC in the UFC: N attempts analysed").
