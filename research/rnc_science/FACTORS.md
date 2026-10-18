# Science-based RNC: what makes a rear-naked choke finish?

Study design for direction #1. Goal: measure which RNC details go with a finish in UFC fights, and say honestly how sure we are.

## Unit of analysis

One **attempt** = from the moment the attacker has back control with the choking arm across the neck, to a finish, an escape or the bell (full rules in `phase3_labels/LABEL_SCHEMA.md`).
**Outcome:** `success` = tap, ref stoppage or unconscious. Everything else = failure.

## Candidate factors

| Factor | Values | How measured | Hypothesis (to test, not assume) |
|---|---|---|---|
| Choke arm position | under_chin / over_jaw / unclear | Reviewer label | Under the chin finishes more often, but "over the jaw" still finishes some fighters (a jaw crank or pain tap) |
| Back control | two_hooks / body_triangle / one_hook / none | Reviewer label | Body triangle keeps control longer, so more time to sink the choke |
| Opponent flattened | yes / no | Reviewer label; later from pose (defender's hip height vs shoulders) | Flattened opponents can't turn in, so higher finish rate |
| Defender two-on-one | yes / no | Reviewer label | Two hands on the choking arm lowers finish rate strongly |
| Second hand | behind_head / palm_to_palm / gable / none | Reviewer label | Behind the head (the "figure-four") finishes most |
| Attacker side | left / right | Reviewer label | Probably no effect. Kept as a sanity check: if this "matters", suspect noise |
| Seconds to lock | number | From timestamps | A fast lock (before the defender sets up hand fighting) finishes more |
| Round / fight time | number | From UFC stats | Fatigue: later rounds finish more |
| Weight class | category | From UFC stats | Lighter classes: more scrambles, lower conversion? |

Pose-derived features come later (Phase 4+): neck–elbow distance, the angle between the attacker's forearm and the defender's jaw line, defender hip height. These turn reviewer labels into measurements.

## Analysis plan

1. **Descriptive first:** the finish rate per factor level, with **Wilson 95% confidence intervals** (an interval that behaves well for small counts and rates near 0% or 100%).
2. **Model:** logistic regression (predicts the log-odds of a finish from the factors) with **standard errors clustered by fighter**. The same fighter appears in several attempts, and those attempts aren't independent.
3. **Optional Bayesian version** (a model that starts from a mild prior belief and updates it with data). Gives "probability the body triangle helps" statements, which read naturally in a write-up.
4. **Pre-register** the hypotheses above in this file *before* looking at the labeled outcomes. That prevents "p-hacking" (trying many cuts until something looks significant).
5. **Multiple comparisons:** about 9 factors are tested, so treat any single p ≈ 0.04 as weak. Report effect sizes and intervals rather than "significant / not".

## How much data do we need? (estimates)

Two-group comparison, about 150 attempts split roughly 75/75, alpha = 0.05:

| True difference in finish rate | Example | Chance we detect it (power) |
|---|---|---|
| 25 points | 55% vs 30% | about 90% |
| 15 points | 45% vs 30% | about 50% |
| 10 points | 40% vs 30% | about 25% |

**Takeaway:** about 150 attempts finds only *big* effects. Smaller effects need 400+ attempts, or pooling with other chokes later (Phase 7). The write-up must say "suggestive" for anything smaller.

## Threats to validity

- **Selection bias:** fights that are easy to find and watch (free YouTube, main events) overrepresent stars. Record the source of every attempt.
- **Label bias:** the reviewer knows the outcome while labeling the details. Mitigation: label details on the clip cut *before* the finish where possible, and have a second person re-label a 20% sample to measure agreement (Cohen's kappa: agreement above chance; aim for > 0.6).
- **Confounding:** better grapplers both use body triangles *and* finish more. Add fighter skill proxies (career submission rate from UFC stats) as controls.
- **Camera cuts:** mark `camera_cut_flag`. Run the analysis with and without flagged attempts.

## Output

- `analysis.ipynb`: tables plus a forest plot (each factor's effect with its interval on one chart).
- A short public write-up: "What actually finishes the RNC in the UFC: N attempts analysed". Derived data only, no footage.
