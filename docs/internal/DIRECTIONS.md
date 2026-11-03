# Project Directions: Scored

Scores are 1–5 and are **judgement calls** (estimates), grounded in the competitor search below.
- **Portfolio:** how much it impresses a CV/ML hiring manager.
- **Difficulty:** 5 = hardest.
- **Uniqueness:** 5 = nobody does this.
- **Profit:** a realistic chance of money without legal blockers.

## Competitor landscape (searched 2026-10)

| Who | What | Overlap with you |
|---|---|---|
| [Jabbr / DeepStrike](https://80.lv/articles/a-tech-startup-introduces-ai-for-combat-sports-analytics/) | Funded startup ([about $5M seed, 2025](https://seedtable.com/companies/jabbr/funding-rounds/seed-2025-10)); CV for **boxing striking**: 50 parameters per boxer, live scoring | Striking, not grappling |
| [UFC × IBM In-Fight Insights](https://www.barchart.com/story/news/36131223/unanimous-decision-ufc-and-ibm-introduce-new-ai-driven-in-fight-insights) | Live milestone and record alerts (since UFC 322) | Stats-based; no submission probability found |
| [Ground CTRL: BJJ](https://apps.apple.com/ae/app/id6763345915), [Roll by KAYYO](https://appshunter.io/ios/app/roll-by-kayyo/id6760706628), [Jiu-Jitsu App](https://mwm.ai/apps/jiu-jitsu-app/6759346698), [RollPlan](https://rollplan.ai/about) | Consumer BJJ apps: upload a roll, get an AI breakdown (Ground CTRL: $9.99/month) | **Crowded.** Position labeling quality is a visible weak spot. |
| [VICOS paper (Hudovernik & Skočaj, 2022)](https://vicos.si/resources/jiujitsu/) | Position detection + automatic BJJ scoring from video | Academic version of the scoring direction |
| Leo Taps (Instagram) | Inspiration; **no public repo or write-up found** across two searches | Unknown method |
| Public datasets | No public RNC/submission attempt-and-outcome dataset found ([HF BJJ set](https://huggingface.co/datasets/carlosj934/BJJ_Positions_Submissions/blob/main/README.md) has 1 sample) | Your Phase 3 data would be a first |

## Blockers to profit (apply to every direction)
- **UFC footage:** copyrighted; downloading violates YouTube/Fight Pass terms. You can't sell or publicly host a product built on it without a license from UFC or a broadcaster.
- **VICOS data:** CC BY-NC-SA, so no commercial use. Any model trained on it inherits NC. A commercial product needs its own position data.
- **Ultralytics YOLO:** AGPL-3.0. Closed-source or SaaS use needs a [paid enterprise license](https://www.ultralytics.com/license). **Use rtmlib/RTMO (Apache-2.0) to stay clean.**
- **Mendeley UFC detection set:** CC BY-NC-SA. FightersMMA (CC BY 4.0) is fine.

## Scoreboard

> **Critique (#17): these scores favor the author's own pick.** A and D score 5 for portfolio even though A's UFC footage can't be shown publicly. D's "difficulty 3" *is* the 50–80 h labeling grind. E (post-fight analytics) is A without its hardest part, yet scores lower. Read the table as a rough sort, not a measurement. The chosen direction (below) is the science write-up, which this table never scored: it's labels-only, so it can be fully shown in public. That makes its portfolio case stronger than A's, and its difficulty is mostly labeling.


| # | Direction | Portfolio | Difficulty | Uniqueness | Profit |
|---|---|---|---|---|---|
| A | UFC broadcast overlay demo (RNC + live finish %) | **5** | 4 | 4 | 1 |
| B | BJJ gym / self-footage coach app | 4 | 4 | 2 | 3 |
| C | BJJ competition position and auto-scoring tool | 3 | 3 | 2 | 2 |
| D | Submission-attempt dataset + benchmark paper | **5** | 3 | **5** | 1 |
| E | Post-fight "submission danger" analytics for commentators/analysts | 4 | 3 | 4 | 2 |
| F | Content / social account (Leo Taps style) | 2 | 2 | 3 | 3 |

### A. Broadcast overlay demo
This is the original vision, and the most striking thing to show: a clip where a probability bar rises and the fighter taps. It's unusual because the funded players work on striking (Jabbr) or stats-only alerts (UFC/IBM), not submission probability from pose. Difficulty is high: broadcast occlusion, cuts and replays, and a small labeled set. **Profit is near zero** without a broadcaster deal, because the product can't exist legally on UFC footage you don't license. The one realistic way to money is using it as a portfolio piece to get hired by Jabbr, Sportlogiq-style analytics companies or a broadcaster's data team.

### B. BJJ gym / self-footage coach app
This has the cleanest legal path, because users upload their own footage. But the market already has several AI roll-analysis apps, at least one charging $9.99/month, so uniqueness is low unless you clearly win on accuracy ("we detect submissions reliably; they mislabel positions"). You'd need your own training data (VICOS is NC) and a non-AGPL stack. Profit potential is moderate, but it's a business with app-store, support and marketing costs, not a weekend project. Strong pivot option later, reusing the A/D tech.

### C. Competition scoring tool
The academic version already exists (the VICOS paper), and IBJJF-style scoring needs very high reliability to be trusted by referees. That makes it hard to sell and only medium impressive. Possible B2B partners exist (Smoothcomp, Flo), but it's a slow sales cycle. Fine as a side feature of A or B, weak as the main project.

### D. Dataset + benchmark paper
No public submission-attempt and outcome dataset exists, so this is genuinely new. Release **labels only**: fight IDs, timestamps, outcomes and the evaluation protocol, plus code. Leave out UFC video and possibly the keypoints (keypoints derived from footage are a legal gray area). A workshop paper (e.g. MMSports at ACM Multimedia, where VICOS published) is a realistic target. It looks very good for ML/research roles. Difficulty is mostly the labeling grind, which you need for A anyway. Profit is about zero directly.

### E. Post-fight analytics ("submission danger" stats)
Example stats: "time in RNC danger", "attempts per minute of back control", "escape rate". These are numbers built from video, and they're new. Analysts, podcasters and fantasy/betting communities would care. Publishing numbers carries less copyright risk than publishing clips. Profit is limited and betting-adjacent, which has its own regulatory and reputation issues. A good *output* of A rather than its own project.

### F. Content account
Easiest to start and could build an audience. But posting UFC clips with overlays risks copyright strikes, and "fair use for commentary" is shaky for full-motion clips. Portfolio value is low unless the technical work is visible (blog/repo). If you do it, use it to *distribute* A and D, not as the project itself.

## ✅ Decision (user, 2026-10-18)

**Core: "Science-based RNC."** Which RNC details predict a finish: arm under the chin vs on the jaw, hooks vs body triangle, flattening, the defender's hand fighting, round, and time held. Each is reported as an effect size with a confidence interval.
**Showcase: the live overlay.** It shows the probability *and* the factors driving it.

Why this works well with the scores above:
- It keeps the uniqueness of A + D.
- It adds something none of the competitors offer: **an explanation**, not just a number. Jabbr counts punches; UFC × IBM reports milestones; the BJJ apps summarize a roll. None quantify *why* a choke finishes.
- It makes a stronger story for both portfolios and BJJ audiences ("under the chin really does matter — here's by how much"). Your BJJ knowledge becomes the edge, because the factor labels need an expert eye.
- It's still feasible: the factors are labeled by you, so the science result doesn't depend on pose quality. Only the *live* overlay does.
- New risk: small samples, so wide CIs. Plan for honest "we can't tell yet" results for some factors (PLAN §5a).

The original reasoning is below for the record.

## Recommendation (original)

**Build A, on top of D: "the first public benchmark for submission-attempt detection and finish prediction in MMA, with a live-probability overlay demo."**

Why:
1. **One body of work gives you two portfolio assets.** The labeling grind (Phase 3) is the dataset (D), and the pipeline (Phases 4–6) is the demo (A).
2. **It's actually unique.** Funded competitors work on striking or stats-only alerts; no public submission dataset exists.
3. **Rigor stands out.** Fight-level splits, a locked test set, leak-free horizons and a stats-only baseline the model must beat are exactly what separates a hire-me project from a tutorial.
4. **It stays legal.** Release labels and code (MIT/Apache) and keep UFC video private; the public demo uses your own gym footage.
5. **It leaves a profit door open.** If you later want money, pivot the same tech to B, retrained on consented gym footage with the Apache-licensed stack.

**Honest bottom line:** Treat this as a career asset, not a business. Expect profit potential near zero unless you pivot to B.
