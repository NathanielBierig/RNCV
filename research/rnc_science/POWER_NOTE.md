# Sample-size note (2026-10-29): is "about 150" the right target?

A dated note, not an amendment: the frozen plan (PREREG v1.0 + A1–A4) is unchanged. Script: [power_recompute.py](power_recompute.py), [output](power_recompute_output.txt). It simulates the exact pre-registered analysis (Firth logistic, profile 95% CIs, §8 verdict rule) with the **real group shares** from the pilot labels: arm under the chin 78%, strong legs 70%, defender two-on-one 32%. Power is the share of simulated studies where the hypothesis comes out *supported*.

| Attempts | H1 arm (coach / pilot effect) | H2 legs (coach / pilot) | H3 two-on-one (coach / pilot) |
|---|---|---|---|
| 100 | 72% / 90% | 30% / 2% | 70% / 25% |
| **150** | **90% / 98%** | 38% / 0% | **90%** / 38% |
| 200 | 98% / 100% | 53% / 0% | 93% / 43% |
| 300 | 98% / 100% | 70% / 5% | 100% / 63% |

Coach effect = what the pre-registration expected (×4, ×2, ×0.3). Pilot effect = model v0.8 estimates (×4.6, ×1.0, ×0.56). 60 simulated studies per cell, so each figure is ±~6 points.

**Reading:**
- **150 stays the target, and now it's justified.** H1 is near-certain to be decided at 150, and H3 too if its effect is as large as coaches think.
- **More attempts don't rescue H2.** If leg control's per-attempt effect is really ~×1 (as the pilot suggests), no sample size will support it. That's consistent with "retention, not finishing". It will be reported as pre-registered (probably *inconclusive*), and the whole-back-exposure analysis ([back_exposures.md](../../reports/back_exposures.md)) tests the retention idea as a clearly labeled exploratory analysis.
- **H3 depends on the true size.** At the pilot's ×0.56, even 300 attempts only reach ~63% power. An *inconclusive* H3 at 150 would not mean the hand fight doesn't matter.

## Update 2026-11-03: labels-only effects and the eligible sample

The earlier scenarios used coach estimates or model v0.8, which includes expert priors. A third scenario uses the labels-only estimates (H1 ×2.8, strong legs ×0.5, H3 ×0.73). The sample sizes are **eligible** attempts: only about 60% of labeled attempts enter the primary model (one-arm chokes, attempts under the minimum length and attempts with no round clock drop out), so 150 labeled is roughly 90 eligible.

| Eligible attempts | H1 supported | H2 supported | H3 supported |
|---|---|---|---|
| 90 (≈150 labeled) | 33% | 0% | 10% |
| 150 (≈250 labeled) | 63% | 0% | 5% |
| 200 | 83% | 0% | 17% |
| 300 | 90% | 0% | 20% |

**Reading:** if the labels-only effects are the true ones, 150 labeled attempts will most likely leave H1 inconclusive too. That doesn't change the frozen plan. It means an "inconclusive" at 150 is the expected result, not a failure, and reaching about 250 labeled attempts is what gives H1 a better-than-even chance (simulated estimates, 60 runs each).
