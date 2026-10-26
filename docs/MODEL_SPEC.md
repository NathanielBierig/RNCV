# Finish model spec: the two numbers on screen and how they're computed

Draft v0.7, 2026-10-26, model-expert session. **v0.7 (§4f):** your structural review: grip by type, body triangle vs two hooks, hidden hand mainly vs the two-on-one, re-attacks. The labels support none of these yet, so they live in the cards. **v0.6 (§4e):** cards = your answers for C1–C4 + the evidence cards for C5–C9; gauge constants from the evidence review (9 s to out, Stellpflug 2020), not fitted. **v0.5 (owner batch 4, §4d):** a figure-four locked under the chin with a two-on-one squeezes at 0.9 of full. Fitting the other squeeze weights to the labels was tried and **rejected**: the labeled positions can't time a finish. **v0.4 (owner batch 3, §4c):** the defender gauge is now **CONSCIOUSNESS** (fast blood-flow deficit + slow lingering fatigue, out after 7.5 s of full squeeze); a late two-on-one keeps only 25% of its effect once the choke is locked under the chin with the hand hidden; fatigue is data-driven (C10 card dropped). v0.3 ran on the owner's bucket answers for C1–C4 (§4b) and adds **attacker fatigue** (§2c, a slow downward drift with time held that starts at zero, so it's not the rejected ramp) and **bucket answers** for cards (§3). v0.2 added the owner's answers (batches 1–2): portfolio showcase, **two** numbers (attacker finish % + defender gauge), priors + data, n ≈ 40–80 attempts, an attempt detector in the next version, and the live model kept separate from the frozen study. Replaces the MVP 0.1 math in `tools/mvp/demo.py` (rejected by the owner).

> **Current model (v0.6, 2026-10-26).** Cards: owner answers C1–C4 + evidence C5–C9 (`research/model/priors_v06.csv`). Finish chance: leave-one-fight-out Brier **0.226** vs 0.270 for always guessing the average (gain not yet certain: 95% CI touches 0). Choke meter (called CONSCIOUSNESS below): physiology constants (9 s from lock to out), not fitted. Pantoja vs Asakura: finish 29% → 93% at the lock → 88% → 100% at the tap; choke meter 0 at 18.0 s (out at 19.0 s). **v0.7c candidate (§4f + coach):** v0.7's structure with the coach review's multipliers as prior means ([run_v07_coach.py](../research/model/run_v07_coach.py)): Brier 0.228 at 2 s / 0.204 over every second (v0.7 alone 0.237 / 0.218). Pantoja 30% → 92% → 88%. Demo: `tools/mvp/demo.py <clip> --model v07c`. **Owner's pick (2026-10-26): v0.7c is the current model**; v0.6 stays as `--model v06`. Everything below is the version log (v0.2 → v0.7).

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## Summary (one screen)

- 🟢 **Why MVP 0.1 read 2% and 30% (three bugs).** (1) A **time ramp** multiplied everything by `1 − e^(−t/9.9 s)`: at most 18% at 2 s and 49% at 6.6 s, whatever the grip. (2) Factor effects were **learned from 34 attempts with no BJJ knowledge**. Some came out backwards (strong legs ×0.66) and others hit the safety caps (arm ×4.0, two-on-one ×0.26). (3) A late two-on-one cut 70% to 38% right before Asakura went out. Result: **2% at 3 s, 33% at the knockout frame.**
- 🟢 **Number 1, attacker FINISH %:** *the chance that this attempt ends in a tap, ref stop or knockout, given what's visible right now.* It's a forecast. It jumps when the position changes, has no time ramp, and reads **100% at the tap frame**. That frame is the event itself, already seen, so it's not peeking at the future.
- 🟢 **Number 2, defender AIR gauge (health bar):** *how much choking the defender has already absorbed.* It drains while a choke is squeezing (fast for a locked choke under the chin, slow over the jaw) and refills once he gets air again. It's a running total of the past, not a forecast. The two disagree in useful ways: "just locked" = high finish %, full air; "survived a long squeeze" = air nearly gone.
- 🟢 **Attacker fatigue (v0.3):** the longer he squeezes, the more his arms and grip tire, so the same position slowly becomes *less* likely to finish. It enters as one extra factor that is **exactly 0 at the start** and grows with seconds of squeezing (≈0.4 after 6 s, 0.8 after 20 s). It can only nudge the number down from where the position puts it, never start an attempt low. It has a matching **GRIP gauge** for the attacker (100 → down). Placeholder prior "80% fresh → 70% after 6 s" + labels gives a small effect (−0.32 log-odds at full fatigue): Pantoja–Asakura 96% → 95%, and 87% → 85% at the end.
- 🟢 **Knowledge = your BJJ judgment + labels.** You give a % (and a range) for ~10 plain-BJJ **scenario cards**, or just a **bucket** (<20 / 20–45 / 45–70 / >70%) when unsure: a bucket counts as 3 attempts, so labels decide. A narrow range counts for more, up to 10 attempts' worth per card. The labels pull the numbers toward what UFC fights actually show. Built for **40–80 attempts**: the cards do real work, and every number carries an **uncertainty band**.
- 🟢 **Prototype (35 attempts, 19 fights, each fight scored by a model that never saw it):** Brier score (0 = perfect, 0.25 = coin flip) is **0.216**, vs 0.270 for always guessing the average and **0.413 for MVP 0.1**. The gain over the average is small and uncertain (95% CI 0.001–0.099). **Pantoja–Asakura:** finish ~35% → **~96%** (figure-four under the chin) → ~87% (late two-on-one) → 100%; air 100 → 0 at 19 s.
- 🟡 **v0.7 (§4f), your structure:** grip by type, body triangle vs hooks, a smaller hidden-hand effect, and a re-attack term (built, but off by default). Brier **0.237** vs 0.226 for v0.6: slightly worse, but within noise (CI −0.004 to +0.023). **The labels don't show any of your four effects yet** (figure-four 47% vs one arm 50%; body triangle 43% vs two hooks 50%; re-attacks can't be tested), and no published study does either. Pantoja: 36% → 90% → 85% → 100%. Pick v0.6 (fits these labels best) or v0.7 (your structure, ready for more labels).
- 🟢 **v0.6 (§4e):** your answers C1–C4 + evidence cards C5–C9 (2 attempts each), gauge constants from published physiology (9 s from lock to out in 81 MMA choke-outs). Brier 0.226 (same as v0.5). The gauge is better timed: **Pantoja consciousness hits 0 at 18.0 s vs out at 19.0 s** (v0.5: 15.7 s), and fewer survivors drop below 20 (7/18 vs 10/18). Pantoja finish %: 29% → 93% → 89% (late two-on-one) → 100%.
- 🟡 **v0.5 (§4d):** finish model unchanged (Brier 0.226). The gauge keeps your 7.5 s and gets your G2 rule. Fitting the squeeze weights to the labels **failed honestly**: settings that stop survivors hitting 0 make real finishes read far too high (Pantoja 47 at the knockout). The labels can't see how deep a choke is, so the gauge stays a "danger dose" based on your numbers. Pantoja: 93% → 90% → 100%; consciousness 0 at 15.7 s (out at 19.0 s). **To make it timeable, log a "fading" moment (Q-D1).**
- 🟢 **v0.4 (§4c):** Brier **0.227**, a tie with v0.3 (0.222; difference +0.004, CI −0.011 to +0.017) and better than the average (0.270). **Pantoja–Asakura:** 32% → **93%** (locked) → 92% (fatigue) → **90%** (late two-on-one now costs only 2 points) → 100%. CONSCIOUSNESS 100 → 7 at 14.9 s → 0 at 16 s (3 s before he went out); Grip 100 → 43.
- 🟢 **v0.3 (superseded by v0.4):** your bucket answers for C1–C4 (3 attempts' worth each), C5–C10 placeholders at lower weight (2 each), and fatigue on. Brier **0.222** vs 0.216 for the v0.2 placeholder cards and 0.270 for the average. That's a statistical tie with v0.2 (+0.006, CI −0.001 to +0.013). Expected: your answers are deliberately wide, and my placeholders were written after seeing the labels. **Pantoja–Asakura:** 29% → **95%** → 94% (fatigue) → 83% (late two-on-one) → 100%; Air 100 → 4 at 18 s; Grip 100 → 46 (§4b).
- 🔴 **Attempt detection is the bottleneck for "drop a clip".** The current detector (frame ROC-AUC 0.70) is "on" for the whole grappling exchange. It puts a correctly placed window on only **~6% of attempts** (start within 2 s, mostly the right span). Target for the app: **≥ 80% of attempts and ≥ 95% of finishes**, start within 2 s, **≤ 1 false alarm per 5-min round**. Until then the app uses a one-key "attempt starts" fallback.
- 🟢 **Science stays separate.** The frozen study is unchanged. The live model can use priors and change freely; **no PREREG amendment is needed for it.** One disclosure note is still needed, because MVP 0.1 showed pilot odds ratios (§8).
- 🔴 **Owner:** answer the question batches in §9 (plain BJJ terms, ~5 min per batch).

---

## 1. Diagnosis: MVP 0.1 in real numbers

`shown = smooth( p(state) × (1 − e^(−t/τ)) )`. `p(state)` = base rate × odds ratios learned from the other fights (an **odds ratio**, OR, is how many times the odds of a finish get multiplied by a factor), +0.5 smoothing, capped to 0.25–4. `τ` = median length of a successful attempt = 9.9 s. Pantoja–Asakura left out ([diagnose_mvp01.py](../research/model/diagnose_mvp01.py)):

| Time | Labeled state | p(state) | ramp | **shown** |
|---|---|---|---|---|
| 2.0 s | arm over the jaw, body triangle, **two-on-one** | 7% (47% base, ×0.5 jaw, ×0.66 legs, ×0.26 two-on-one) | 0.18 | 7% |
| 3.0 s | same | 7% | 0.26 | **2%** |
| 6.6 s | figure-four under the chin, hand tucked, no two-on-one | 70% | 0.49 | 8% → 31% |
| 14.9 s | two-on-one again | 38% | 0.78 | 43% → 31% |
| 19.0 s | **unconscious** | — | — | **33%** |

Every attempt in the file read 7–10% at 2 s, because `ramp(2 s) = 0.18`. The ramp answers a different question ("has it already finished by now?"). In survival terms it's backwards: an attempt that has lasted 15 s is, if anything, *less* likely to finish than a fresh one in the same position.

## 2. The two numbers, defined

**State** = what's visible right now, from the labels: arm under the chin / over the jaw; grip locked (figure-four, palm-to-palm, gable, wrist pull) or not (one arm, short choke); strong legs (body triangle or two hooks); defender two-on-one; chin tucked; choking hand tucked; defender flattened. It's the 2-s values plus the G-panel changes logged so far, never a future change. Unclear or blank fields count as halfway.

### 2a. Attacker FINISH % (a forecast)
- **Definition:** `F(t) = P(this attempt ends in tap / ref stop / unconscious | state at t, attempt still on)`. It's the same idea as NFL/NBA live win probability (Lock & Nettleton 2014): the chance from this moment on.
- **Math:** logistic regression, `logit F = a + Σ b_k · x_k(state)`. Logistic regression turns a sum of factor "points" into a 0–100% chance. Each `b_k` comes from your cards + labels (§3).
- **Uncertainty:** an 80% band from the model's own uncertainty (the Laplace approximation). It's drawn as a thin bracket around the number. Pantoja–Asakura: 10–74% (arm over the jaw, mostly unknown territory) → 80–99% (locked) → 58–97% (late two-on-one). With 40–80 attempts the band *is* the honest message.
- **Ends:** tap / ref stop / knockout frame → 100%. Escape / position change → 0%. Bell → 0% ("saved", Q-D2).
- **Optional "fading" state** (Q-D1): arms drop, body goes slack, ref leans in, logged with G. It lets F reach ~95% a second *before* the tap, still without seeing the future. This needs a new label field (main session).

### 2b. Defender AIR gauge (v0.2–v0.3; replaced by the CONSCIOUSNESS gauge in §4c)

> v0.4: Air is superseded. The owner pointed out that an RNC is a **blood** choke, not an air choke, and that it fatigues a lot. The new two-part gauge is defined in §4c; this section is kept for the record.

- **Definition:** `Air(t) = 100 × (1 − E(t) / E_out)`, floored at 0, where `E(t)` = **squeeze exposure**, the seconds of effective choking absorbed so far:
  - `dE/dt = s(state) − recovery`. `s` = how hard the visible state squeezes, from 0 to 1: a locked choke under the chin = 1, over the jaw ≈ 0.15, and a two-on-one or a tucked chin takes some of it away. **Recovery** = `E / 8 s`, applied only while the squeeze is light (s < 0.3), i.e. once he's breathing again.
  - `E_out` = seconds of full squeeze until a UFC fighter goes out. Placeholder **9 s**: full blockage of the neck arteries causes unconsciousness in ~6–7 s (Rossen, Kabat & Anderson 1943), and fight chokes are rarely full. It wasn't tuned on any clip.
- **What it's for:** showing that time under a real choke matters *physiologically*, without the finish % becoming a time ramp. The finish % says where the attempt is heading; Air says how much has already been done.
- **How they relate:** both come from the same state, but F is a probability and Air is a dose. In v2 the dose can enter F as one extra factor (`b_air × (1 − Air/100)`), with its prior from a card like "same position, but he's already been squeezed 6 s" (Q-C10). Today Air is display only. Air is set to 0 at a finish frame and refills after an escape.
- **Sanity check (placeholder weights, no fitting):** median Air at the end is **24 for finishes vs 50 for non-finishes** (AUC 0.67; 8/17 finishes and 6/18 non-finishes end at ≤ 20). As expected for a dose, long failed squeezes (Oliveira–Holloway) also drain it. **Pantoja–Asakura: 100 → 84 at 8 s → 48 at 12 s → 16 at 16 s → 0 at 19 s.** The match with the knockout time was not tuned.

### 2c. Attacker fatigue and the GRIP gauge (v0.3)
- **Idea (owner):** the choker's forearms and grip fade the longer he squeezes, so with the *same visible position* the finish chance drifts down over time.
- **Squeeze effort so far:** `G(t)` = seconds of squeezing, weighted by how hard the position squeezes (the same `s(state)` as the Air gauge). There's no recovery inside an attempt.
- **Fatigue factor:** `fatigue(t) = 1 − e^(−G/12 s)`. It's **0 at the start**, ≈0.4 after 6 s of full squeeze, ≈0.8 after 20 s, and never above 1.
- **In the finish model:** one extra term, `logit F = … + b_fat · fatigue(t)`.
- **Why this is not the rejected ramp:** the ramp *multiplied* the number by something that started at 0, so every attempt began near 0%. Here the term starts at **0 effect**: a locked choke reads high from the first second, and fatigue can only shave a little off as seconds pass. Its size `b_fat` is learned (card + labels), not fixed.
- **Prior:** card C10, "same position (C4), but he's already squeezed ~6 s" (placeholder: 80% fresh → 70%).
- **Prototype:** with that card + 35 attempts, `b_fat = −0.32` (×0.72 on the odds at full fatigue). That's small, and the labels can neither confirm nor refute it. Brier is unchanged (0.215 vs 0.216). Pantoja–Asakura: 96% → 95% over the locked phase, 87% → 85% at the end.
- **GRIP gauge (attacker, mirrors Air):** `Grip(t) = 100 × e^(−G/12 s)`, 100 → about 45 for Pantoja at the knockout. It's display + model input.
- **Honest caveat: Air and fatigue are both built from squeeze time.** The labels can only measure their **net** effect ("does time under the choke help or hurt?"). Air pulls toward a finish (he's fading); fatigue pulls away (he's tiring), and long squeezes that fail are also *survivors*, i.e. good defenders. So the display shows both gauges, but the model has **one** time term whose sign and size come from your cards + labels. With 40–80 attempts, expect it to stay small and uncertain.
- Later refinement: carry fatigue across repeated attempts in the same round (e.g. Oliveira–Holloway, 4 attempts), with recovery between them.

## 3. Your knowledge + labels: elicitation and updating

**Elicitation protocol** (a light version of SHELF, O'Hagan et al. 2006; cards = "conditional-means priors", Bedrick, Christensen & Johnson 1996):
1. **Scenario cards in BJJ terms.** Each card is one visible position, e.g. *"Figure-four under the chin, body triangle, his hands not two-on-one, chin not tucked."* You answer: **"Out of 100 of these in the UFC, how many get finished?"** plus a **range** ("at least __, at most __"). Cards come in batches of 4–5, so you never need to think in odds ratios.
2. **Weight from your range.** A card becomes pretend data (Greenland 2007): mean p with a range read as 90% → equivalent number of attempts `n0 = p(1−p)/sd² − 1`, `sd = (high − low)/3.29`, **capped at 10** because experts' ranges are usually too narrow. For example, 80% with range 30–95 → 3 attempts' worth; 80% with range 60–90 → 10 (cap). No range → 4.
2b. **Bucket option (when you can't give a %; v0.3).** Answer with a coarse bucket: **<20%**, **20–45%**, **45–70%**, **>70%**. The card is set at the bucket's center (10%, 32.5%, 57.5%, 85%) with a weight of only **3 attempts** (a wide prior: Beta(0.3, 2.7) for "<20", up to Beta(2.55, 0.45) for ">70"). That way the labels dominate wherever you're unsure. Prototype: converting all 8 placeholder cards to buckets costs almost nothing (Brier 0.220 vs 0.216). You can upgrade a bucket to an exact % + range later for the cards you feel sure about.
3. **Feedback round.** The fitted model shows you 3–4 *new* positions it was never told about, with its %. If one looks wrong to you, that's a new card. This catches contradictions between cards.
4. **Gauge questions** (Air): seconds to "out" under a full squeeze; how hard different positions squeeze (0–10); how fast a fighter recovers.

**How labels update the cards:** labels count one attempt each, split over its positions by time (each attempt counts once however long it lasts). For example, a card at 80% weighing 4 + 12 real attempts in that position finishing at 50% → ~57%. A "sample" term absorbs the fact that labeled fights are picked from the finish list (49% finish here). The overlay therefore shows the real-world level set by your base-rate answer until the random-10 fights are labeled (PREREG §2).

**Expected behavior at n ≈ 40–80 (estimates):** at 40 attempts ~10 cards × 4 ≈ 40 pretend attempts, so cards and labels share the say. At 80, labels lead in common positions (under the chin + locked), while cards still decide rare ones (locked over the jaw, no hooks). The bands narrow by roughly 1/√n: about 30% narrower at 80 than at 40.

## 4. Prototype results (placeholder cards, written by me)

35 attempts (the 0.4-s bell attempt left out), 19 fights, 17 finishes, leave-one-fight-out. [state_model.py](../research/model/state_model.py), output in [state_model_output.txt](../research/model/state_model_output.txt).

| Model | Brier at 2 s | Brier over every second | Log loss at 2 s |
|---|---|---|---|
| Always the average | 0.270 | 0.270 | 0.733 |
| MVP 0.1 (rejected) | **0.413** | 0.337 | 1.258 |
| Labels only, no cards | 0.219 | 0.195 | 0.620 |
| Cards only, no labels | 0.216 | 0.202 | 0.617 |
| **Cards + labels (recommended)** | **0.216** | **0.192** | **0.615** |

Calibration at the 2-s landmark (does "70%" happen 70% of the time?):

| Predicted | n | Mean predicted | Observed | 95% CI |
|---|---|---|---|---|
| 0–20% | 3 | 14% | 33% | 6–79% |
| 20–40% | 11 | 31% | 36% | 15–65% |
| 40–60% | 13 | 51% | 38% | 18–64% |
| 60–80% | 5 | 68% | 80% | 38–96% |
| 80–100% | 3 | 93% | 100% | 44–100% |

Honest reading: the ordering is right and nothing is wildly off, but 35 attempts can't prove calibration. Fight-clustered bootstrap: cards + labels beat the average by 0.054 (CI 0.001–0.099) and tie labels-only (−0.003, CI −0.022 to +0.012). **Today the cards buy sensible behavior** (no backwards effects, no "2% with an arm under the chin"), **not measurable accuracy.** Caveat: my placeholder cards were written after seeing the label file, and you've watched these fights, so card-vs-label agreement here is optimistic. The real test is new fights.

## 4b. v0.3 results: your bucket cards + fatigue (the MVP 0.2 model)

Cards ([priors_owner.csv](../research/model/priors_owner.csv)):
- **Your answers:** C1 any attempt = 20–45%, coded as "every field unknown". C2 = <20%. C3 = 45–70%. C4 = >70%. Each is a wide prior worth 3 attempts.
- **Placeholders C5–C10:** kept, but **lower weight (2 attempts each)** until you answer them.
- **Fatigue term:** on.

Run: [run_v03.py](../research/model/run_v03.py), output in [run_v03_output.txt](../research/model/run_v03_output.txt). 35 attempts, 19 fights, leave-one-fight-out.

| Model | Brier at 2 s | Brier over every second | Log loss at 2 s |
|---|---|---|---|
| Always the average | 0.270 | 0.270 | 0.733 |
| v0.2 placeholder cards, no fatigue | 0.216 | 0.192 | 0.615 |
| v0.3 your buckets, no fatigue | 0.223 | 0.197 | 0.635 |
| **v0.3 your buckets + fatigue** | **0.222** | **0.196** | **0.632** |

Fight-clustered bootstrap, v0.3 + fatigue minus …:
- **The average:** −0.047 (CI −0.094 to +0.008). Better on average, but the CI now just touches 0.
- **v0.2 placeholders:** +0.006 (CI −0.001 to +0.013). A tie, slightly worse.
- **No fatigue:** −0.001 (CI −0.004 to +0.002). Fatigue makes no measurable difference yet.

**Reading:** your answers are wide on purpose, so the labels do more of the work. My v0.2 placeholders were written after I'd seen the label file, so their small edge is partly hindsight. On this data v0.3 is as good as v0.2 and **more honest**. The fitted fatigue effect is −0.35 log-odds at full fatigue (×0.70 on the odds): small, and pulled mostly from the C10 placeholder.

Calibration at the 2-s landmark:

| Predicted | n | Mean predicted | Observed | 95% CI |
|---|---|---|---|---|
| 0–20% | 5 | 14% | 40% | 12–77% |
| 20–40% | 9 | 34% | 33% | 12–65% |
| 40–60% | 10 | 51% | 40% | 17–69% |
| 60–80% | 8 | 66% | 62% | 31–86% |
| 80–100% | 3 | 91% | 100% | 44–100% |

The lowest bin under-predicts (2 of 5 finished at ~14%), but n = 5. Watch it as labels grow.

**Pantoja–Asakura R2** (fight left out; what MVP 0.2 would show, real-world scale):

| Time | Visible state | Finish % | 80% band | Air | Grip |
|---|---|---|---|---|---|
| 0–6.6 s | arm over the jaw, grip unclear, body triangle, two-on-one, chin tucked | **29%** | 7–67% | 100 → 97 | 100 → 96 |
| 6.6–14.9 s | figure-four under the chin, hand tucked, no two-on-one | **95% → 94%** (fatigue) | 78–99% | 93 → 26 | 94 → 57 |
| 14.9–19.0 s | Asakura two-on-one again | **83%** | 50–96% | 22 → 4 | 55 → 48 |
| 19.0 s | **unconscious** (event shown) | **100%** | — | 0 | 46 |

All three owner complaints are fixed: an arm under the chin with the figure-four reads 95%, not 2%; the knockout moment reads 83% and then 100%, not 30%; the tap/knockout frame reads 100%.

## 4c. v0.4: owner batch 3 (the model for MVP 0.2)

**Changes:**
1. **Late two-on-one in a deep lock (Q-D4, "matters a little").** The two-on-one factor is multiplied by `1 − 0.75 × deep`, where `deep = arm under chin × grip locked × hand hidden` (each 0–1, unknown = 0.5). In a full deep lock a two-on-one keeps **25%** of its usual effect (`DEEP_TWO_ON_ONE_KEEP = 0.25`). It's a fixed rule from your answer; 35 attempts can't test it. The same rule also softens the two-on-one's effect on squeeze strength.
2. **Fatigue (C10, "no preference").** The C10 card is dropped. The fatigue term now has only a weak prior centered on zero (normal, sd 1.5 on log-odds), so its size comes from the labels. Fitted: **−0.54** log-odds at full fatigue (×0.58 on the odds). It's larger than in v0.3 but very uncertain.
3. **CONSCIOUSNESS gauge (G1 + G3), replacing Air.** Suggested on-screen label: **CONSCIOUSNESS**, a bar with two shaded parts: "blood flow" (fast) and "fatigue" (lingering).
   - `B` = blood-flow deficit, `D` = lingering fatigue (both in "seconds of full squeeze"), `s(state)` = squeeze strength 0–1 (as before).
   - While squeezing: `dB/dt = 0.7·s`, `dD/dt = 0.3·s`, so a continuous full squeeze reaches `B + D = 7.5 s` → **consciousness 0 after 7.5 s** (G1: "5–10 s").
   - When the squeeze is light (`s < 0.3`): `B` drains with a **3-s** time constant (blood flow comes back quickly) and `D` with a **120-s** one (it doesn't recover within the exchange).
   - `CONSCIOUSNESS = 100 × max(0, 1 − (B + D)/7.5)`. `B` and `D` carry over between attempts in the same round, recovering over the gap.
   - **Display rules for Main:** floor the bar at 5 until a finish event (so it never reads 0 while he's still defending), snap to 0 at a finish frame, and let it refill after an escape (blood part fast, fatigue part stays).

**Exact constants:** `DEEP_TWO_ON_ONE_KEEP = 0.25`; `FATIGUE_SCALE = 12.0 s` (unchanged); `CONSCIOUSNESS = {secs_to_out: 7.5, lingering_share: 0.3, blood_recovery_secs: 3.0, fatigue_recovery_secs: 120.0, light_below: 0.3}`; squeeze weights unchanged (placeholders until G2). Cards: [priors_owner_v04.csv](../research/model/priors_owner_v04.csv) (C1–C4 your buckets at weight 3, C5–C9 placeholders at weight 2, no C10). Run: [run_v04.py](../research/model/run_v04.py) → [run_v04_output.txt](../research/model/run_v04_output.txt).

| Model (LOFO, 35 attempts / 19 fights) | Brier at 2 s | Brier over every second | Log loss at 2 s |
|---|---|---|---|
| Always the average | 0.270 | 0.270 | 0.733 |
| v0.3 (buckets + C10 card + fatigue) | 0.222 | 0.196 | 0.632 |
| v0.4 without the deep-lock rule | 0.223 | 0.196 | 0.632 |
| **v0.4** | **0.227** | **0.205** | **0.643** |

v0.4 minus v0.3: +0.004 (CI −0.011 to +0.017), a tie. v0.4 minus the average: −0.043 (CI −0.088 to +0.009). The deep-lock rule costs a little on these labels: in this sample, attempts that kept a two-on-one late often still escaped. That's a judgment call the labels can't settle at n = 35. It's your BJJ view against a handful of attempts, and §7's checks will show if it hurts as data grows.

Calibration at 2 s: 0–20% → 25% observed (n = 4), 20–40% → 57% (n = 7), 40–60% → 25% (n = 12), 60–80% → 67% (n = 9), 80–100% → 100% (n = 3). Noisy; the middle bins swap.

**Consciousness gauge check** (end of attempt, carried across a round): median **0 for finishes vs 15 for non-finishes** (AUC 0.63); ≤ 20 at the end: 11/17 finishes, **10/18 non-finishes**. The gauge drains too readily on attempts that were survived. Likely cause: the placeholder squeeze strengths (G2), since labels can't see how hard he's actually squeezing. Your G2 answers are the fix; until then, read the gauge as "danger dose", not "he's out".

**Pantoja–Asakura R2** (fight left out; MVP 0.2 values):

| Time | Visible state | Finish % (80% band) | CONSCIOUSNESS (blood / fatigue deficit, s) | Grip |
|---|---|---|---|---|
| 0–6.6 s | arm over the jaw, two-on-one, chin tucked | **32%** (9–70%) | 100 → 97 (0.1 / 0.1) | 100 → 96 |
| 6.6 s | figure-four under the chin, hand hidden | **93%** (75–99%) | 97 | 96 |
| 10 s | same | 93% | 60 (2.0 / 1.0) | 77 |
| 14.9 s | late two-on-one | **90%** (65–98%), was 83% in v0.3 | 7 (4.8 / 2.1) | 55 |
| 16–18 s | same | 90% | 0 → floor 5 on screen (6.4 / 2.8) | 52 → 46 |
| 19.0 s | **unconscious** (event shown) | **100%** | 0 | 43 |

## 4d. v0.5: owner batch 4 (G2) and the label calibration of the gauge

**Owner G2:** figure-four locked under the chin **with** a two-on-one = "almost full" squeeze. Coded as a two-on-one relief of **0.10** when the choke is locked under the chin (`two_relief_locked`), vs **0.35** otherwise. Over the jaw and one arm: no preference, so those weights were left for the labels to decide.

**The calibration you asked for** ([calibrate_squeeze.py](../research/model/calibrate_squeeze.py), leave-one-fight-out, weak priors at the v0.4 values):
- **Fitted:** squeeze over the jaw, squeeze under the chin with one arm, how much a tucked chin relieves, and seconds to out.
- **Target:** a finished attempt's gauge hits 0 at its labeled end (±2 s); a survived attempt's gauge stays ≥ 20.

| Setting | Finishes at 0 within ±2 s of the end | Survivors wrongly at 0 (below 20) | Pantoja–Asakura |
|---|---|---|---|
| v0.4 (before) | 3/17 (7 early, 7 late) | 6/18 (10/18) | 0 at 16.0 s |
| **v0.5 = v0.4 + G2 (default)** | 4/17 (7 early, 6 late) | 6/18 (11/18) | **0 at 15.7 s** (out at 19.0) |
| Label-fitted, your target (LOFO) | 4/17 (1 early, **12 late**) | **1/18** (3/18) | **47** just before the knockout, never 0 |
| Label-fitted, "tap-aware" target (tap ⇒ ≤ 40) | 2/17 (4 early, 11 late) | 4/18 (5/18) | 0 at 26.9 s |
| Label-fitted + "tucked chin helps little once locked" | 0/17 (17 late) | 1/18 (1/18) | seconds to out runs away to **26 s** |

Label-fitted constants (your target): over the jaw 0.06 (was 0.15), one arm 0.61 (0.45), tucked-chin relief 0.70 (0.30), seconds to out 7.8 (7.5). All of these sit at or near the edge of their weak priors.

**Why it fails (the important finding):**
- **Survivors spend a long time in positions labeled "locked under the chin"** (Oliveira–Holloway: 29 s and 34 s; Blachowicz–Pereira). Finishes reach the same labels and end in 5–10 s.
- The visible fields can't tell a choke that's really sinking from one that's labeled locked but isn't biting. So any setting that spares the survivors also slows the gauge on real finishes.
- **Taps come before unconsciousness**, so "0 at the tap" is the wrong target for 13 of the 17 finishes. Only 4 are knockouts.

**Decision for MVP 0.2 (recommended): owner-anchored gauge, v0.5 default.**
- **Settings:** your 7.5 s, your G2 rule, v0.4 weights for the rest.
- **Display rules:** floor at 5 until a finish event, snap to 0 at the finish, refill after an escape.
- **What it means:** the gauge reads as "danger dose if the choke is truly on", **not a prediction of the moment he goes out**. It drops early on deep chokes that are survived (6/18), and the floor keeps that honest.
- **Alternative:** the label-fitted preset is in the code as `SQUEEZE_V05_FIT` / `CONSCIOUSNESS_V05_FIT`, if you'd rather it never drops on survivors at the cost of finishes reading high.

**What would make the gauge timeable (needs labels, Main/owner):**
1. **"Fading"** (Q-D1): the moment his arms drop or he goes limp.
2. **"Choke biting"**: yes/no, the squeeze is visibly sinking (face color, the defender stops fighting the hand and grabs the forearm, the attacker arches). Either would let the fit separate real chokes from labeled-locked-but-not-sinking ones. It would need an A2-style label field, live-model only (no PREREG change for the overlay).

Finish model: unchanged apart from the squeeze feeding the fatigue term. LOFO Brier **0.226** (v0.4 0.227; difference −0.000, CI −0.001 to +0.001); fatigue −0.59 log-odds at full fatigue. Output: [run_v05_output.txt](../research/model/run_v05_output.txt), [calibrate_squeeze_output.txt](../research/model/calibrate_squeeze_output.txt) (+ `_tapaware`, `_chinrule`).

**Pantoja–Asakura, v0.5 default:**

| Time | Finish % (80% band) | Squeeze | CONSCIOUSNESS | Grip |
|---|---|---|---|---|
| 0–6.6 s | 32–33% (9–70%) | 0.07 | 100 → 97 | 100 → 96 |
| 6.6 s (figure-four under the chin) | **93%** (75–99%) | 0.80 | 97 | 96 |
| 10 s | 93% | 0.80 | 60 | 77 |
| 14.9 s (late two-on-one) | **90%** (65–98%) | 0.72 | 7 | 55 |
| 15.7 s on | 89–90% | 0.72 | 0 → shown as 5 (floor) | 52 → 46 |
| 19.0 s **unconscious** | **100%** | — | 0 | 43 |

**Exact constants for Main:**
- `SQUEEZE_V05 = {w_jaw 0.15, w_one_arm 0.45, chin_relief 0.30, two_relief_open 0.35, two_relief_locked 0.10, hand_bonus 0.15}`
- `CONSCIOUSNESS_V05 = {secs_to_out 7.5, lingering_share 0.3, blood_recovery_secs 3.0, fatigue_recovery_secs 120.0, light_below 0.3}`
- `DEEP_TWO_ON_ONE_KEEP 0.25`, `FATIGUE_SCALE 12.0`
- These are the defaults in `state_model.py`.

## 4e. v0.6: evidence review + your cards (the model for MVP 0.2)

Source: [research/priors_evidence/EVIDENCE.md](../research/priors_evidence/EVIDENCE.md) (bjj-research session), with `priors_evidence.csv` and `gauge_evidence.csv`.

**Cards** ([priors_v06.csv](../research/model/priors_v06.csv)): **your answer wherever you gave one, evidence elsewhere.**
- **C1–C4: your buckets** (3 attempts each). The evidence agrees on C1 (35%, 22–50), C2 (8%) and C4 (72%).
- 🟡 **C3 mild disagreement:** you said 45–70%; the evidence says ~35% (15–60) and the labels show 1/4. The ranges overlap. I used yours; if more labels keep showing late two-on-ones escaping, this is the card to revisit.
- **C5–C9: evidence cards** at **2 attempts each.** The evidence session set them at 2.5; I lowered them because they were sanity-checked against the same `labels.csv` the model fits, which would otherwise count part of the labels twice.
- No fatigue card; fatigue stays data-driven (−0.57 log-odds at full fatigue).

**Gauge constants** (evidence values, **not fitted to the labels**):
- **Seconds to out: 9.0.** Lock to unconscious averaged 9.0 s in 81 MMA choke-outs (95% CI 8.3–9.9; RNC 8.9 s; Stellpflug et al. 2020). It's the upper end of your "5–10 s".
- **Blood recovery: 3 s** (revival 4–8 s after release).
- **Lingering share: 0.2** and **fatigue recovery: 60 s** (low confidence).
- **Squeeze over the jaw: 0.05** (the jawbone shields the carotids).
- Unchanged: one arm 0.45 (evidence 0.5, 0.3–0.7: same within its range), tucked-chin relief 0.30, **locked + two-on-one 0.9 (your G2 kept** over the evidence's 0.55, which has no study behind it).

**Calibration attempt with evidence priors:** I re-ran §4d's label fit with these values as priors ([calibrate_squeeze_evidence_output.txt](../research/model/calibrate_squeeze_evidence_output.txt)). It again pushed the weights to protect survivors (tucked-chin relief 0.30 → 0.69; finishes then read late, Pantoja never 0). Same reason as in §4d: the labels can't see whether a choke is biting. **The plain evidence values do best on the counts that matter, so v0.6 uses them unfitted.**

| Gauge setting | Finishes at 0 in the last 2 s before the end | Finishes out too early | Survivors at 0 | Survivors below 20 | Pantoja 0 at (out at 19.0 s) |
|---|---|---|---|---|---|
| v0.5 (7.5 s, v0.4 weights + G2) | 3/17 | 7 | 6/18 | 10/18 | 15.7 s |
| **v0.6 (evidence constants)** | 4/17 (7/17 if "within 2 s after" also counts) | **3** | 6/18 | **7/18** | **18.0 s** |

Finish model ([run_v06_output.txt](../research/model/run_v06_output.txt)): LOFO Brier **0.226** (v0.5 0.226; difference −0.000, CI −0.002 to +0.002); vs the average −0.044 (CI −0.088 to +0.008). For comparison, Main's `priors_combined.csv` (owner **and** evidence cards both on C1–C4) scores 0.229, and Pantoja reads about 3 points lower. I recommend `priors_v06.csv`: it doesn't count C1–C4 twice.

**Pantoja–Asakura, v0.6:**

| Time | Finish % (80% band) | Squeeze | CONSCIOUSNESS | Grip |
|---|---|---|---|---|
| 0–6.6 s (arm over the jaw, two-on-one) | **29%** (8–67%) | 0.02 | 100 → 99 | 100 → 99 |
| 6.6 s (figure-four under the chin, hand hidden) | **93%** (73–98%) | 0.80 | 99 | 99 |
| 10 s | 92% | 0.80 | 69 | 79 |
| 14.9 s (late two-on-one) | **89%** (63–97%) | 0.72 | 25 | 57 |
| 17 s | 88% | 0.72 | 8 | 50 |
| 18.0 s | 88% | 0.72 | **0** (shown as 5) | 47 |
| 19.0 s **unconscious** | **100%** | — | 0 | 44 |

**Exact constants for Main** (already the `state_model.py` defaults: `SQUEEZE_V06`, `CONSCIOUSNESS_V06`):
- Squeeze: `w_jaw 0.05, w_one_arm 0.45, chin_relief 0.30, two_relief_open 0.35, two_relief_locked 0.10, hand_bonus 0.15`
- Gauge: `secs_to_out 9.0, lingering_share 0.2, blood_recovery_secs 3.0, fatigue_recovery_secs 60.0, light_below 0.3`
- `DEEP_TWO_ON_ONE_KEEP 0.25`, `FATIGUE_SCALE 12.0`
- Cards: `priors_v06.csv`. Display rules as in v0.4/v0.5 (floor 5 until a finish frame, snap to 0 at the finish, refill after an escape).

## 4f. v0.7: your structural review (grip type, body triangle, hidden hand, re-attacks)

Code: [model_v07.py](../research/model/model_v07.py) (separate module; v0.2–v0.6 stay reproducible). Cards: [priors_v07.csv](../research/model/priors_v07.csv). Label counts: [label_checks_v07_output.txt](../research/model/label_checks_v07_output.txt). Run: [model_v07_output.txt](../research/model/model_v07_output.txt). The evidence addendum (bjj-research, 2026-10-26) is merged.

**What the labels say** (35 attempts, finish-enriched, so compare levels with each other, not with the real world; 95% CIs are huge):

| Your belief | Raw label counts (finish / attempts, at the 2-s mark) | Published evidence |
|---|---|---|
| Figure-four > other locks > one arm | figure-four **9/19 (47%)**; wrist pull 2/4; palm-to-palm 1/1; one arm **4/8 (50%)**. Arm under the chin only: figure-four 8/13 (62%), one arm 4/6 (67%) | 🔴 no study compares grips |
| Body triangle > two hooks | body triangle **6/14 (43%)**; two hooks **5/10 (50%)**; one hook 4/9; none 2/2 | 🔴 no retention or finish data; consensus says the triangle is harder to escape |
| Hidden hand matters mainly against a two-on-one | hidden + no two-on-one **5/5**; hidden + two-on-one 2/6; not hidden + two-on-one 1/4; neither 9/20. If anything it helped most *without* a two-on-one, but n = 5 | consensus: the hidden hand blocks the peel |
| Re-attacks finish more (defender tired) | finish-list rounds: the last attempt **7/7**, earlier attempts **0/10**, **by construction** (we label the round that ended in the finish). Candidate rounds: 0/8 overall. Attempts carrying a lot of earlier fatigue mostly escaped (3/9) | 🔴 no study; grip strength drops after BJJ bouts (Andreato 2014); suggested OR ~1.1 per earlier attempt (0.8–1.5) |

**How v0.7 builds them in:**
1. **Grip by type:** separate figure-four and other-lock (palm-to-palm / gable / wrist pull) factors, both vs unlocked (one arm / short choke). New placeholder cards put them in your order: C4 figure-four + body triangle open 85% (your bucket), **C12** same with another lock **65%**, **C13** one arm **40%**.
2. **Body triangle vs two hooks:** separate factors; **C14** figure-four + *two hooks* open **75%** vs C4's body triangle 85%.
3. **Hidden hand:** it mainly works against the defender's hands. In a lock under the chin it cuts a two-on-one to 25% of its effect, as before. Its own effect now has a tight prior (sd 0.5 log-odds), so it can't reach ×1.7 without strong data. Removing the own effect entirely cost Brier +0.012.
4. **Re-attacks:** `def_fatigue = 1 − e^(−D0 / 1 s)`, where D0 = the defender's lingering fatigue carried from earlier attempts in the round (the gauge's slow part). It's about 0.65–0.98 after a real earlier squeeze. The labels can't test it, so they're kept out of its fit; only card **C15** (C4 on a re-attack: 87%, weight 2, about the evidence's OR 1.1) sets it. **Off by default:** on these labels it costs Brier +0.011, and the data-driven version even points the other way (×0.64). Turn it on (`USE_REATTACK = True`) once random-fight rounds exist to test it.
5. **Kept:** arm under the chin, flattened, two-on-one, chin, attacker fatigue, and the gauge (9 s, 3-s blood recovery, lingering fatigue). C7 (locked over the jaw) is now 15% (evidence addendum: jaw cranks do finish UFC fights, ~2% of back-control neck finishes).

| Model (LOFO, 35 attempts / 19 fights) | Brier at 2 s | Brier over every second | Log loss |
|---|---|---|---|
| Always the average | 0.270 | 0.270 | 0.733 |
| **v0.6** | **0.226** | **0.205** | **0.644** |
| **v0.7** (re-attack off) | **0.237** | 0.218 | 0.666 |
| v0.7 + re-attack (card only) | 0.248 | 0.228 | 0.691 |
| v0.7 + re-attack (card + labels) | 0.239 | 0.221 | 0.668 |

v0.7 minus v0.6: +0.011 (95% CI −0.004 to +0.023), i.e. slightly worse but not clearly. Ablations: the grip/legs split costs about +0.01, the re-attack term +0.011. That's expected: each split adds factors the labels can't support yet, so they mostly add noise.

**v0.7 weights in plain words** (all data; odds multiplier with 80% range; cards alone in the third column):

| Factor | × odds | 80% range | Cards alone | In words |
|---|---|---|---|---|
| Arm under the chin (vs over the jaw) | **×3.7** | 1.4–9.9 | ×2.1 | the biggest, most certain effect |
| Defender flattened | **×4.4** | 1.5–13 | ×1.2 | big in the labels (6/6 finished), tiny n |
| Figure-four (vs one arm) | **×2.0** | 0.9–4.5 | ×2.6 | the labels pull it down from your cards |
| Other lock: palm / gable / wrist pull (vs one arm) | **×1.8** | 0.7–5.2 | ×1.2 | the labels pull it up: nearly equal to figure-four |
| Body triangle (vs one hook / none) | ×1.1 | 0.5–2.4 | ×1.5 | the labels erase your edge for now |
| Two hooks (vs one hook / none) | ×1.1 | 0.4–2.8 | ×1.25 | same |
| Defender two-on-one (open choke) | **×0.43** | 0.18–1.0 | ×0.49 | cuts the odds by more than half; in a deep lock with the hand hidden only 25% of that |
| Choking hand hidden (own effect) | ×1.24 | 0.7–2.2 | ×1.0 | smaller than v0.6's ×1.7, as you wanted |
| Chin tucked | ×1.0 | 0.45–2.4 | ×0.7 | no signal |
| Attacker fatigue (full) | ×0.64 | 0.13–3.0 | ×1.0 | drifts the number down with time held |
| Re-attack fatigue (if turned on) | ×1.56 | 0.3–7.6 | card C15 | the card's view; the labels alone say ×0.64 |

**Pantoja–Asakura, v0.7** (fight left out): **36%** (arm over the jaw, grip unclear, two-on-one; 80% band 11–73%) → **90%** at 6.6 s (figure-four under the chin, hand hidden; 67–97%) → 89% at 10 s → **85%** after the late two-on-one (57–96%) → **100%** at the knockout (19.0 s). Consciousness (unchanged gauge) 99 → 69 at 10 s → 25 at 14.9 s → 0 at 18.0 s.

**Recommendation:** v0.7 has the structure you want and is ready for more labels. The new cards C12–C15 are placeholders that need your %s (buckets are fine). On today's 35 attempts v0.6 is a little more accurate. Either is fine for MVP 0.2; if v0.7, keep the re-attack term off until random-fight rounds exist. **The decision is yours.**

## 5. Other designs considered
- **B. Competing-risks hazard model (switch at ~100+ attempts).** Each second the attempt finishes, fails or continues (a discrete-time hazard model: Allison 1982; Singer & Willett 2003; competing risks: Putter et al. 2007). The bell **censors**: the observation stops without an outcome. It handles the round clock properly (less time left → lower finish %), gives a "danger in the next 3 s" readout, and matches PREREG §7's secondary model. Too few finishes (17) to fit today.
- **C. Points rubric + calibration curve.** Fully transparent, but the points aren't a probability until calibrated, and 40–80 attempts can't calibrate a curve. Design A is the same idea with the calibration built in.

## 6. Automation: attempt detector → model

**Pipeline for "drop a clip":**
1. Frame scores (CLIP image features + logistic, 2 frames/s) → ~2-s moving average.
2. **Hysteresis gate:** the attempt turns ON when the score is above a threshold and OFF after 2 s below a lower one. It's a yes/no gate. **Never multiply the finish % by the detector's confidence**: with a 0.70-AUC detector that would bring back the crushed numbers of MVP 0.1. Show the detector's confidence separately as a small "attempt detected" tag.
3. While ON: the finish % and Air run on the **state**. In the next version the state comes from labels when the clip is labeled. On an unlabeled clip it comes from **in-app hotkeys** (3–4 keys: arm under chin, locked, two-on-one, chin tucked), or else all-unknown, which gives an honest "generic attempt" ~30% with a wide band. Later, automatic factor classifiers can replace the keys.
4. Design A doesn't use time since the start, so a detector that starts 1–3 s late barely changes the finish %. Air starts draining late, though, and that's visible.

**What each detector error does on screen:**
- A **missed attempt** = no number, and a tap comes out of nowhere. That's the worst case for a demo, so finishes must be caught.
- A **false alarm** = a generic ~30% that appears and fades.
- A **late start** = mostly harmless.

**Accuracy needed (event level, targets for a public demo, estimates):**

| Metric | Target | Now (crop model, 19 clips, [detector_events.py](../research/model/detector_events.py)) |
|---|---|---|
| Attempts with a correctly placed window (start within 2 s, overlap ≥ 30%) | **≥ 80%** (≥ 95% of finishes) | **~6%** at any threshold |
| Any overlap with the attempt | ≥ 90% | 86–94% at threshold 0.4–0.5, but the windows span the whole exchange |
| False alarms | **≤ 1 per 5-min round** (0.2/min) | 0.1–0.4/min, measured on only 16 min of mostly near-attempt footage (optimistic) |

Roughly, a frame ROC-AUC of about 0.9 with sharp start/end edges is needed. That's an estimate: frame AUC alone doesn't guarantee good windows, as 0.70 shows.

**Plan to get there (estimates):**
1. **Hard negatives:** full rounds with back control but *no* choke, and other ground grappling. Without them the false-alarm rate can't be measured. The candidate rounds already watched as `watched_no_rnc` are the cheapest source.
2. **Temporal features:** a 2–4 s window of CLIP features (mean + change), so the model sees "the arm comes across" instead of "two men on the ground".
3. **Two stages:** "back control?" (easier), then "arm across the neck?" on a head-region crop.
4. **Score at event level every time**, not frame AUC. Re-test at ~40 fights.

Until the target is met, the app's honest mode is **"press A when the arm goes across"** (a one-key start), with the detector shown as a suggestion.

## 7. Validation plan (rerun on every card or label change)
1. Leave-one-fight-out Brier, log loss and Brier skill vs "always the average", at 2 s and over every second.
2. Calibration table (5 bins until 150+ attempts) with Wilson CIs, and band coverage (do 80% bands contain the outcome-consistent value ~80% of the time?).
3. Complaint checks: locked figure-four under the chin ≥ 70%; Pantoja–Asakura ≥ 75% in the last 5 s; tap frame = 100%.
4. Air: median Air at the end for finishes vs non-finishes; the knockout cases should be near 0.
5. Detector: the event-level table above.
6. Hold out the next ~10 newly labeled fights: score once, never tune on them.

## 8. Science framing (PREREG check)
- 🟢 **The frozen study stays as is.** "Which states at a fixed 2-s moment go with a finish" (Firth logistic, H1–H3, bell censored) is still a clean question. The 2-s landmark is what keeps long attempts from leaking the outcome.
- 🟢 **The live predictor is its own model: a product, not an analysis.** It may use your priors, post-landmark states, "bell = 0", the Air gauge, and change freely. **No PREREG amendment is needed for any of that,** as long as none of it is reported as a study result.
- 🔴 **Still needed, one dated disclosure note (A5):** MVP 0.1 (`8d8ee7f`) fit and **displayed** pilot odds ratios (arm 4.0, legs 0.66, two-on-one 0.26) on 34 attempts, and this prototype fits factor effects on 35. A3/A4 say "before any outcome was tabulated or any factor model was fitted". No hypothesis, coding or rule changed, so it's not fatal, but the record should say when pilot estimates were first seen. Not made by me.
- ⚠ **Would need an amendment only if:** the PREREG's secondary hazard model (§7) is fit *with* your priors (keep a prior-free version for the study), or a new "fading" field enters that hazard model (A2 lists its time-varying fields).
- ⚠ Your cards aren't blind (you've labeled these fights). Fine for the overlay, never for the study.
- ⚠ No `random_fight` rows yet, so any "X% of UFC RNC attempts finish" claim waits for the random-10 fights.

## 9. QUESTIONS FOR THE OWNER 🔴 (Main relays in batches)

For every card: **"Out of 100 of these in the UFC, how many end in a tap or knockout? And your range: at least __, at most __."** If unsure, just pick a bucket: **<20 / 20–45 / 45–70 / >70%**. Think elite UFC defense, not gym rolls.

**Batch 1: the core (5 cards)**
- **C1** Any rear-naked choke attempt at all: arm across the neck, second hand working to lock it. (Placeholder: 30%)
- **C2** Arm **over the jaw**, no lock yet, one hook in, he has **two hands on the choking arm**, chin tucked. (8%)
- **C3** Arm **under the chin**, **figure-four locked**, **body triangle**, but he has two hands on the arm and his chin tucked. (45%)
- **C4** Same as C3, but his hands are **not** both on the arm and his **chin isn't tucked**. (80%)
- **C5** C4 + **choking hand hidden deep** behind the head/on the biceps + he's **flattened** on his belly. (90%)

**Batch 2: the edges (5 cards)**
- **C6** Arm under the chin, **one arm only** (no second hand yet), one hook, two hands on the arm, chin tucked. (20%)
- **C7** **Locked grip but over the jaw**, body triangle, two hands on the arm, chin tucked. (20%)
- **C8** Figure-four under the chin, **no hooks at all** (e.g. from turtle/standing), hands not two-on-one, chin not tucked. (65%)
- **C9** Figure-four under the chin + body triangle, two hands on the arm, but **chin NOT tucked**. (55%)
- **C10 (fatigue)** C4, but the attacker has **already been squeezing hard for ~6 s** and it hasn't gone yet: out of 100, how many still get finished? (A bucket is fine.) (70%)
- **C11 (fatigue)** Same, after **~15 s** of squeezing. (Implied by the C10 placeholder alone: ~60%.)

**Batch 3: the defender gauge (Air)**
- **G1** A fully locked RNC under the chin, squeezing hard: how many seconds until a UFC fighter taps or goes out? (9 s)
- **G2** On a 0–10 scale, how hard do these squeeze? Over the jaw, no lock (placeholder 1.5) · under the chin, one arm (4.5) · under the chin, locked (10) · locked but he has two hands on the arm (6.5).
- **G3** After he breaks the grip, how many seconds until he's "fresh" again? (8 s)

**Batch 4: definitions (one line each)**
- **Q-D1 Fading:** would you log a "fading / going limp" moment with G? It lets the number hit ~95% *before* the tap.
- **Q-D2 Bell:** round ends mid-choke → show 0% ("saved") or freeze the last number?
- **Q-D3 Wrist pull (Dagestani grip):** count it as locked, like a figure-four? (Placeholder: yes)
- **Q-D4 Late two-on-one:** once the figure-four is locked and the hand is hidden, does grabbing the arm with both hands still matter? A lot / a little / not at all. (Pantoja–Asakura's last 4 s: −9 points now.)
- **Q-D5 App mode until the detector is good:** OK to have the user press one key when the arm goes across?

## 10. Sources (standard references)
- Live win probability: Lock & Nettleton (2014), *J. Quant. Anal. Sports* 10(2); Yurko, Ventura & Horowitz (2019), *JQAS* 15(3) (nflWAR); Stern (1994), *JASA* 89.
- Dynamic prediction / landmarking: van Houwelingen (2007), *Scand. J. Stat.* 34.
- Discrete-time hazards, competing risks: Allison (1982), *Sociological Methodology* 13; Singer & Willett (2003), *Applied Longitudinal Data Analysis*; Putter, Fiocco & Geskus (2007), *Stat. Med.* 26.
- Expert priors: Bedrick, Christensen & Johnson (1996), *JASA* 91; Greenland (2007), *Int. J. Epidemiol.* 36; O'Hagan et al. (2006), *Uncertain Judgements* (SHELF; experts' ranges run narrow).
- Small-data logistic: Firth (1993), *Biometrika* 80; Gelman et al. (2008), *Ann. Appl. Stat.* 2; Riley et al. (2020), *BMJ* 368.
- Outcome-based sampling: Prentice & Pyke (1979), *Biometrika* 66; King & Zeng (2001), *Political Analysis* 9.
- Calibration: Brier (1950), *Mon. Weather Rev.* 78; Van Calster et al. (2019), *BMC Medicine* 17.
- Choke physiology: Rossen, Kabat & Anderson (1943), *Arch. Neurol. Psychiatry* 50 (unconsciousness ~6–7 s after full arterial blockage).

## 11. Files and hand-off to Main
- [research/model/state_model.py](../research/model/state_model.py): finish model (fit, Laplace bands, leave-one-fight-out scores, calibration), the Air gauge (`health_trace`), and card weights from ranges (`card_weight`). Run: `python -I research/model/state_model.py [--priors <cards.csv>]`.
- [research/model/priors_placeholder.csv](../research/model/priors_placeholder.csv): 9 placeholder cards (8 positions + C10 fatigue). Your answers go into `priors_owner.csv` with the same columns, plus optional `p_low,p_high` or `bucket` (`<20`, `20-45`, `45-70`, `>70`). `USE_FATIGUE` in `state_model.py` switches the fatigue term on (runs M5); M6 = all cards as buckets.
- **v0.7:** `model_v07.py` (`fit_cov`, `x_at`, `segments`, `encode`; run `D0.update(round_d0(rows))` once for re-attacks) + `priors_v07.csv`; `sm.predict` / `sm.interval` work on its vectors. Gauge unchanged (v0.6). **v0.6:** `state_model.py` defaults + `priors_v06.csv`.
- **v0.5 (use this for MVP 0.2):** same wiring as v0.4; `state_model.py` defaults are now v0.5 (`SQUEEZE_V05`, `CONSCIOUSNESS_V05`); `run_v05.py` reproduces §4d. v0.4 wiring for reference: cards [priors_owner_v04.csv](../research/model/priors_owner_v04.csv); `sm.USE_FATIGUE = True` (`DEEP_TWO_ON_ONE_KEEP = 0.25` is the default); finish % as below; defender bar = `sm.consciousness_trace(row, start=(B, D))` (columns t, consciousness, blood deficit, lingering fatigue; carry `(B, D)` between attempts in a round, decayed over the gap as in `run_v04.round_gauges`); label **CONSCIOUSNESS** with "blood flow" / "fatigue" shading; floor 5 until a finish frame.
- [research/model/priors_owner.csv](../research/model/priors_owner.csv): the v0.3 cards (kept for the record) (your buckets C1–C4 + lower-weight placeholders C5–C10). [run_v03.py](../research/model/run_v03.py) reproduces §4b. For MVP 0.2: `sm.USE_FATIGUE = True; beta = sm.fit(other_fights_rows, cards("priors_owner.csv"))`; per frame `x = sm.x_at(row, t)` → `sm.predict(beta, x, sample=False)` and `sm.interval(...)`.
- [research/model/detector_events.py](../research/model/detector_events.py): event-level detector check (clip venv).
- [research/model/diagnose_mvp01.py](../research/model/diagnose_mvp01.py): reproduces the MVP 0.1 numbers.
- For `tools/mvp/demo.py` (Main): replace `fit`/`finish_prob` and the ramp with `state_model.fit` + `predict(..., sample=False)` (+ `interval` for the band); drive the defender bar with `health_trace` instead of `1 − finish %`; drive the attacker GRIP gauge from the same squeeze effort `G` (`100·e^(−G/12)`); snap to 100% / Air 0 at a finish frame and 0% at an escape; drop the 3-s post-event easing.
