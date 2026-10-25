# Evidence-based priors for the finish model (cards C1–C9 + consciousness gauge)

2026-10-26, evidence-research session. Inputs for `docs/MODEL_SPEC.md` §3/§4c. Files: [priors_evidence.csv](priors_evidence.csv) (cards, same columns as `research/model/priors_owner_v04.csv`, plus `ev_low/ev_high/confidence`), [gauge_evidence.csv](gauge_evidence.csv) (gauge constants).

🟢 solid (peer-reviewed, measured) · 🟡 partial (one source or indirect) · 🔴 not studied (judgment + consensus) · ⚪ open

## Summary (one screen)

- 🟢 **Time to out under a locked choke ≈ 9 s.** In 81 MMA choke-outs, from "fully locked" to unconscious took a mean of **9.0 s** (95% CI 8.3–9.9). The RNC averaged 8.9 s, with no difference between choke types (Stellpflug et al. 2020). Full lab occlusion is faster, **~6.8 s** (Rossen et al. 1943; Nimura et al. 2022 review). → **secs_to_out 9.0** (range 7–11), up from 7.5. The repo agrees: the median labeled attempt lasts 9.8 s to a tap and 11.8 s to unconscious, and both counts include the time before the lock.
- 🟢 **Recovery is fast.** People wake **4–8 s** after release (7–12 s for one judo choke) (Nimura 2022). → **blood_recovery_secs 3** (keep).
- 🟡 **Lingering effects are real after a choke-out, but unmeasured after partial squeezes.** 61.5% of judo choke-outs showed convulsions or staggering after waking, more when release came ≥ 4 s after unconsciousness (Sasaki et al. 2022). EEG changes lasted ~20 s (Rau et al. 1998). Fighter-pilot blackouts (G-LOC, the nearest analog) leave ~28 s of total impairment. → **lingering_share 0.2, fatigue_recovery_secs 60** (low confidence; 120 s is also defensible).
- 🟡 **Base rate: 30–45% of UFC RNC attempts finish.** The only per-attempt figure is **41%** (Fightnomics/CagePotato, UFC 2007–~2013, single source, method unverified). Repo stats give ~28% for *all* submission types per scored attempt. RNC is the most efficient submission (guillotine 14%, kimura/shoulder locks 6%). → **C1 = 35%** (22–50).
- 🔴 **Configuration effects (jaw vs chin, grip type, hooks, two-on-one, chin tuck) have no quantitative study at all.** What exists: instructional consensus (over the jaw = pain + slow; the two-on-one is the main defense; a hidden back hand blocks the peel) and the repo's own 36 labels (finish-enriched). Those cards are labeled **low confidence**, have wide ranges, and weigh 2.5 attempts each.
- ⚠ **Double counting:** I cross-checked cards against `labels.csv`, the data the model also fits. I set p from physiology and consensus first and used the labels only as a sanity check. Even so, don't give these cards more weight than the n0 column does.
- **Owner vs evidence:** C1, C2 and C4 agree. **C3 disagrees mildly:** the owner said 45–70, the evidence says ~35% (15–60). G1 "5–10 s" agrees, at the upper end.

## Q1. Time to unconsciousness, recovery, lingering effects

| Finding | Number | Source | Grade |
|---|---|---|---|
| Lock → LOC (loss of consciousness), resisting MMA fighters, 81 choke-outs, expert panel timed it from video | **9.0 s** (CI 8.3–9.9); RNC 8.9; bulldog 6.2 – von Flue 10.5; no sig. difference by type | Stellpflug, Menton, Dummer, Menton, Corry & LeFevere (2020), *Int J Perf Anal Sport* 20(4):720–728, [doi:10.1080/24748668.2020.1780873](https://doi.org/10.1080/24748668.2020.1780873); [summary](https://combatsportslaw.com/2020/06/17/study-locked-in-chokes-take-9-seconds-to-full-unconsciousness/) | 🟢 (no SD per type; "fully locked" judged by experts) |
| Full neck-cuff occlusion (600 mmHg) → LOC | ~6.4–6.9 s | Rossen, Kabat & Anderson (1943), *Arch Neurol Psychiatry* 50; data in [DTIC ADA255485](https://apps.dtic.mil/sti/pdfs/ADA255485.pdf), [Smith 2007 revisit](https://litfl.com/wp-content/uploads/2019/09/Smith-2007-Acute-Arrest-of-Cerebral-Circulation-in-Man-Revisited.pdf) | 🟢 |
| Judo choke review: compression → LOC; LOC → revival | **6.8 s**; revival **4–8 s** (kata-juji-jime 6–10 s / 7–12 s); mechanism = carotid ischemia, carotid-sinus reflex minor; anoxic convulsions common | Nimura, Higaki, Motohashi & Yokoyama (2022), *Arts & Sciences of Judo* 2(1):36–44, [record](https://lida.sport-iat.de/djb/Record/4077472) | 🟢 (review of small old experiments) |
| Brain flow during a judo choke | middle cerebral artery flow 37.9 → 4.2 cm/s (n = 9) | Raschka et al., cited in a 2002 judo paper (found via a search summary, not checked at source) | 🟡 |
| Elite judo, 7,426 bouts: after-effects | 39 LOCs; 61.5% convulsions/staggers after waking; release ≥ 4 s after LOC → OR 6.7 for symptoms | Sasaki et al. (2022), *J Sci Med Sport* 25(11):942–947, [doi:10.1016/j.jsams.2022.09.001](https://doi.org/10.1016/j.jsams.2022.09.001) | 🟢 |
| EEG after ~8-s judo chokes | slow waves; changes significant up to ~20 s after | Rau, Raschka, Brunner & Banzer (1998), [record](https://www.bisp-surf.de/Record/PU199810305089) (n = 6) | 🟡 |
| Brain blood flow just after recovery | lower in 6/7 choked judoka | Rodriguez et al. (1991), [author listing](https://infomus.academia.edu/GuidoRodriguez) (abstract only) | 🟡 |
| Analog: G-LOC (fighter-pilot blackout) incapacitation | ~12 s absolute + ~16 s confused = ~28 s | Whinnery (USAF centrifuge), [StatPearls](https://statpearls.com/point-of-care/31890) | 🟡 analog |
| Mechanism isn't only the carotids | jugular compression (↑ intracranial pressure) + vagal drop in blood pressure also contribute | review, *Int J Neurosci* (2019), [summary](https://combatsportslaw.com/2019/09/11/study-the-science-behind-the-rear-naked-choke/) | 🟡 |
| UFC: 904 choke finishes 1993–2020; RNC 49.1%; 11% ended unconscious | (repo labels: 4/17 finishes unconscious, a finish-enriched sample) | Stellpflug (2020), [PMID 33347362](https://pubmed.ncbi.nlm.nih.gov/33347362/); [summary](https://combatsportslaw.com/2020/12/26/physician-reviews-and-analyzes-all-choke-submissions-in-ufc-history/) | 🟢 |

**Not studied:** how fast a *partial* squeeze drains consciousness; recovery after a sub-LOC squeeze; any dose-response curve. The gauge's linear "seconds of full squeeze" is a modeling choice, not physiology.

## Q2. RNC configurations

| Factor | Evidence | Direction / size used | Grade |
|---|---|---|---|
| Arm under the chin vs over the jaw | Over the jaw = pain-based, slower; often makes him lift the chin so the arm slips under ([Kesting 2009](https://www.grapplearts.com/?p=365)). The mandible keeps the forearm off the carotids (anatomy). Forearm on the windpipe = painful, slower air choke ([Danaher via BJJEE 2020](https://www.bjjee.com/articles/john-danaher-shares-the-secret-to-the-perfect-rear-naked-choke-set-up/)). Labels: under chin 15/26 vs over jaw 2/8 | large: squeeze 1.0 vs 0.05; C2 8%, C7 12% | 🔴 consensus + 🟢 physiology |
| Figure-four vs palm-to-palm vs gable vs wrist pull | **No study.** Stellpflug 2020: no time difference across 11 locked choke types → once locked, the grip style likely matters less than *whether* it's locked. Labels: figure-four 9/20, wrist pull 2/4, palm-to-palm 1/1 | treat every lock as equal (supports Q-D3 "wrist pull = locked") | 🔴 |
| One arm (no second hand) | No study; one-arm/short chokes do finish UFC fights; labels one_arm 4/8 | squeeze 0.5; C6 18% (5–40) | 🔴 |
| Hooks / body triangle | No study. Physiology: legs don't change the squeeze; they stop the turn-in/stand-up escape. Labels show no gradient (BT 6/15, two hooks 5/10, one hook 4/9) | C8 (no hooks) 60% vs C4 72% | 🔴 |
| Defender two-on-one | Consensus: the main defense, mostly before the lock; after the lock it's used to peel the back hand. Labels (under chin + locked): with two-on-one 1/4, without 10/14 | big before the lock; C3 35% vs C4 72%; keep the deep-lock 25% rule (owner) but the labels hint it matters more | 🔴 |
| Chin tuck | Consensus: blocks the arm from getting under; little effect once under. Labels: tucked 13/28 vs not 4/8 (no signal) | small; C9 50% vs C3 35% | 🔴 |
| Hand hidden / flattened | Consensus: hidden hand blocks the peel; flattening removes the turn-in. Labels (under + locked): hand tucked 6/7; flattened 6/6 | C5 85% | 🔴 (tiny n) |

## Q3. Base rates (UFC)

| Source | What it measures | Number |
|---|---|---|
| Kuhn / Fightnomics, "CagePotato Databomb #2" ([repost](https://www.lowkickmma.com/cagepotato-databomb-2-breaking-down-submission-success-rates-in-ufc-fights/), now 404; quoted via search snippets) | RNC attempts that end in a tap/nap, UFC since 2007 (~2013) | **41%** (guillotine 14%, shoulder locks 6%); method not verified 🟡 |
| Repo [summary_stats.json](../../phase3_labels/summary_stats.json) / [README](../../phase3_labels/README.md) | all submission finishes per UFC-scored attempt (finishes 1,733; scored attempts in non-finish rounds 4,472) | **~28%** for any submission (an upper-ish bound: failed attempts in finish rounds are missing) 🟢 |
| Repo | RNC share of submission finishes | 683 / 1,733 = **39%** (published: 32.7–49%, depending on sample) |
| Repo labels.csv (36 RNC attempts) | finish-enriched sample | 47% (finish_list 17/27, candidate rounds 0/9); not a base rate |

**Reconciliation:** RNC beats the all-submission average (41% vs ~28%). But this project's attempt definition (arm across + second hand working, video-coded) catches brief attempts that scorers skip, which pulls the rate down. → **C1 35% (22–50), medium.** The owner's 20–45 bucket matches. The random-10 fights will give the first unbiased check (PREREG §2).

## Q4. Translation into model inputs

**Cards** ([priors_evidence.csv](priors_evidence.csv)). Weight `n0` by confidence: medium 4, low 2.5. I put the ranges in `ev_low/ev_high`, not `p_low/p_high`, because `card_weight()` would turn these 90% ranges into the 10-attempt cap, too strong for unstudied cards.

| Card | Evidence % (range) | Conf. | Owner v0.4 | Agree? |
|---|---|---|---|---|
| C1 any attempt | **35** (22–50) | medium | 20–45 | 🟢 yes |
| C2 jaw, no lock, defended | **8** (2–20) | medium | <20 | 🟢 yes |
| C3 locked under chin + BT, two-on-one + chin tucked | **35** (15–60) | low | 45–70 | 🟡 evidence lower; ranges overlap |
| C4 locked under chin + BT, open | **72** (50–88) | medium | >70 (85) | 🟢 yes (owner a bit higher) |
| C5 C4 + hand hidden + flattened | **85** (65–95) | low | placeholder 90 | 🟢 |
| C6 under chin, one arm, defended | **18** (5–40) | low | placeholder 20 | 🟢 |
| C7 locked over the jaw, defended | **15** (5–35) (was 12; addendum) | low | placeholder 20 | 🟡 a bit lower |
| C8 locked under chin, no hooks, open | **60** (35–80) | low | placeholder 65 | 🟢 |
| C9 C3 but chin not tucked | **50** (28–72) | low | placeholder 55 | 🟢 |

**Gauge** ([gauge_evidence.csv](gauge_evidence.csv)):

| Constant | v0.4 | Evidence | Conf. |
|---|---|---|---|
| secs_to_out | 7.5 | **9.0** (7–11) | high |
| blood_recovery_secs | 3 | **3** (2–6) | medium |
| lingering_share | 0.3 | **0.2** (0.1–0.4) | low |
| fatigue_recovery_secs | 120 | **60** (20–180) | low |
| squeeze: locked under chin / one arm / locked + two-on-one / jaw no lock / locked jaw | 1.0 / 0.45 / 0.65 / 0.15 / ~0.2 | **1.0 / 0.5 / 0.55 / 0.08 / 0.25** (jaw values raised in the addendum) | medium / low / low / low / low |
| chin-tuck multiplier | 0.7 | 0.7 (0.5–0.9) | low |

The lower jaw squeeze (0.15 → 0.05) and the lower two-on-one squeeze target the v0.4 problem where the gauge drained on 10/18 *survived* attempts. Whether it actually fixes it is ⚪ untested; the model-expert session should rerun.

## What's solid vs speculative
- 🟢 Solid: ~9 s from lock to out in MMA; ~7 s under full occlusion; 4–8 s revival; post-LOC symptoms; RNC = the most common and most efficient UFC submission.
- 🟡 Partial: the 41% per-attempt rate (one source, method unseen); lingering-effect duration (EEG and G-LOC analogs).
- 🔴 Not studied anywhere I could find: finish rates by arm position, grip type, hooks, two-on-one or chin tuck; squeeze strength by configuration. Those numbers are judgment from mechanics + coaching consensus + 36 biased labels. I found **no** biomechanics paper measuring neck pressure by RNC configuration, and no Danaher text that quantifies these.
- Not used: Mitchell et al. 2012 (*J Appl Physiol*, vascular neck restraint, police volunteers). I saw only secondary police summaries, no time figures. The "10–20 s" figure on Wikipedia is unsourced.

---

## ADDENDUM (2026-10-26): owner's follow-up checks for v0.7

Grades as above. Changed numbers are in [priors_evidence.csv](priors_evidence.csv) (C7) and [gauge_evidence.csv](gauge_evidence.csv) (grip, jaw and re-attack rows).

| # | Question | Verdict | Suggested model numbers | Conf. |
|---|---|---|---|---|
| A1 | Is the figure-four stronger than palm-to-palm / gable / wrist pull / short choke / one arm? | 🔴 **No study measures it**: no grip-force or neck-pressure paper, and no submission statistics by RNC grip (BJJ Heroes, ADCC and IBJJF tallies count "RNC" only). Stellpflug 2020 found no time difference across 11 *choke types*, which says nothing about grips. Single-source claim (Wikipedia RNC, one citation): palm-to-palm = more pressure, less head control, more air/mixed choke → more pain, slower. Repo labels: figure-four 9/20, wrist pull 2/4, palm-to-palm 1/1, one arm 4/8 (no signal at n = 36). | Finish %: **every two-hand lock counts as "locked"**, with no grip-type term. Squeeze: figure-four 1.0, palm-to-palm / gable / short choke 0.9 (0.7–1.0), wrist pull 0.85 (0.6–1.0), one arm 0.5 (0.3–0.7) | low |
| A2 | Body triangle vs two hooks | 🔴 **No retention or finish data anywhere.** Consensus ([Wikipedia: body triangle](https://en.wikipedia.org/wiki/Body_triangle_(grappling)); coaching articles): the body triangle is harder to escape and stops the defender from clearing hooks with his legs, but limits the attacker's own movement. Another coach argues upper-body control matters more than the legs ([Open Note Grappling 2023](https://www.opennotegrappling.com/p/rear-naked-choke-components)). Repo labels: finish rate body triangle 6/15, two hooks 5/10, one hook 4/9; failed attempts that ended in escape: 4/9 vs 3/5 vs 3/5; re-attack after a failure ~100% in every group (biased sample). **Owner's re-attack point:** plausible (keeping the back = more attempts), and Oliveira–Poirier fits it (body triangle, 2 attempts, the 2nd tapped). But no data, and a re-attack effect belongs to the *round* (more attempts), not to each attempt's finish %. | Keep one `legs_strong` factor (body triangle ≈ two hooks), prior OR ≈ 1.7 vs no hooks (cards C4 vs C8). Optional small body-triangle bump OR 1.15 (0.8–1.6). Model the owner's re-attack point as "attempts per round", not per-attempt finish % | low |
| A3 | Over the jaw: does it ever choke? | 🟡 **It does finish UFC fights, mostly as a pain/crank tap.** ufcstats (repo raw_sources) logs **13 "Neck Crank From (Standing) Back Control" finishes vs 679 RNC** (~2% of back-control neck finishes; e.g. Cirkunov–Nicholson 2016 cracked the jaw, [report](https://www.lowkickmma.com/misha-cirkunov-cracks-alex-nicholsons-jaw-for-submission-win/); Pantoja–Perez 2022). Some finishes recorded as "RNC" are over the jaw too. In the repo, Oliveira–Poirier UFC 269 was labeled over the jaw throughout and ended in a tap (1 of 17 labeled finishes). Physiology: **no measurement exists.** By anatomy, the forearm on the mandible sits above the carotid bifurcation (~C3–C4), so blood flow is blocked only partly, through the biceps/forearm "V" on the sides of the neck. Coaches say it's slow and painful and often makes him lift the chin so the arm slips under ([Kesting 2009](https://www.grapplearts.com/?p=365)). | Squeeze: jaw unlocked **0.08** (was 0.05; 0–0.2), jaw locked **0.25** (0.1–0.45). C7 **15%** (5–35). Jaw finishes come from pain, which the CONSCIOUSNESS gauge can't show; they belong in the finish %, not the gauge | low |
| A4 | Re-attacks / defender fatigue: do later chokes finish more often? | 🔴 **No study of re-attack success.** Indirect: dominant grip strength falls after BJJ bouts (Andreato et al. 2014, *Kinesiology* 46(1):44–52, [record](https://hrcak.srce.hr/123721), n = 12); BJJ athletes tire in the upper limbs earlier across repeated matches (2020 *JSAMS* systematic review, [record](https://lida.sport-iat.de/djb/Record/4061459?lng=en); no high-quality studies). Blood flow comes back in 4–8 s (Nimura 2022), so leftover "hypoxia" matters only for quick regrips. Repo: 6 of 17 re-attack gaps ≤ 6 s, 11 of 17 ≤ 20 s. **The repo labels can't answer it:** a finish ends the round, so later attempts only follow failures (raw: first attempts 10/19 finish, later 7/17). | Keep carrying the CONSCIOUSNESS gauge (blood + fatigue deficit) across attempts in a round (it already captures quick regrips). Optional defender-fatigue term: **OR 1.1 per earlier attempt in the round** (0.8–1.5), prior centered near no effect. Better: add a `prior_attempts_in_round` field when labeling the random-10 fights | low |

**Bottom line for v0.7:** none of the four has measured support beyond the physiology (A3 anatomy, A4 recovery time). Treat grip type, body triangle vs hooks and re-attacks as owner judgment with wide priors. The one data-backed change is that over-the-jaw squeezes *do* finish UFC fights (~2% of back-control neck finishes, plus some logged as RNC), so jaw squeeze and C7 go up slightly.
