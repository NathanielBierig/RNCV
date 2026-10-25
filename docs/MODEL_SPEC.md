# Finish model spec: the two numbers on screen and how they're computed

Draft v0.3, 2026-10-25, model-expert session. v0.3 runs on the owner's bucket answers for C1–C4 (§4b) and adds **attacker fatigue** (§2c, a slow downward drift with time held that starts at zero, so it's not the rejected ramp) and **bucket answers** for cards (§3). v0.2 added the owner's answers (batches 1–2): portfolio showcase, **two** numbers (attacker finish % + defender gauge), priors + data, n ≈ 40–80 attempts, an attempt detector in the next version, and the live model kept separate from the frozen study. Replaces the MVP 0.1 math in `tools/mvp/demo.py` (rejected by the owner).

🟢 done · 🟡 in progress · 🔴 needs the owner · ⚪ not started

## Summary (one screen)

- 🟢 **Why MVP 0.1 read 2% and 30% (three bugs).** (1) A **time ramp** multiplied everything by `1 − e^(−t/9.9 s)`: at most 18% at 2 s and 49% at 6.6 s, whatever the grip. (2) Factor effects were **learned from 34 attempts with no BJJ knowledge**. Some came out backwards (strong legs ×0.66) and others hit the safety caps (arm ×4.0, two-on-one ×0.26). (3) A late two-on-one cut 70% to 38% right before Asakura went out. Result: **2% at 3 s, 33% at the knockout frame.**
- 🟢 **Number 1, attacker FINISH %:** *the chance that this attempt ends in a tap, ref stop or knockout, given what's visible right now.* It's a forecast. It jumps when the position changes, has no time ramp, and reads **100% at the tap frame**. That frame is the event itself, already seen, so it's not peeking at the future.
- 🟢 **Number 2, defender AIR gauge (health bar):** *how much choking the defender has already absorbed.* It drains while a choke is squeezing (fast for a locked choke under the chin, slow over the jaw) and refills once he gets air again. It's a running total of the past, not a forecast. The two disagree in useful ways: "just locked" = high finish %, full air; "survived a long squeeze" = air nearly gone.
- 🟢 **Attacker fatigue (v0.3):** the longer he squeezes, the more his arms and grip tire, so the same position slowly becomes *less* likely to finish. It enters as one extra factor that is **exactly 0 at the start** and grows with seconds of squeezing (≈0.4 after 6 s, 0.8 after 20 s). It can only nudge the number down from where the position puts it, never start an attempt low. It has a matching **GRIP gauge** for the attacker (100 → down). Placeholder prior "80% fresh → 70% after 6 s" + labels gives a small effect (−0.32 log-odds at full fatigue): Pantoja–Asakura 96% → 95%, and 87% → 85% at the end.
- 🟢 **Knowledge = your BJJ judgment + labels.** You give a % (and a range) for ~10 plain-BJJ **scenario cards**, or just a **bucket** (<20 / 20–45 / 45–70 / >70%) when unsure: a bucket counts as 3 attempts, so labels decide. A narrow range counts for more, up to 10 attempts' worth per card. The labels pull the numbers toward what UFC fights actually show. Built for **40–80 attempts**: the cards do real work, and every number carries an **uncertainty band**.
- 🟢 **Prototype (35 attempts, 19 fights, each fight scored by a model that never saw it):** Brier score (0 = perfect, 0.25 = coin flip) is **0.216**, vs 0.270 for always guessing the average and **0.413 for MVP 0.1**. The gain over the average is small and uncertain (95% CI 0.001–0.099). **Pantoja–Asakura:** finish ~35% → **~96%** (figure-four under the chin) → ~87% (late two-on-one) → 100%; air 100 → 0 at 19 s.
- 🟢 **v0.3 = the model for MVP 0.2:** your bucket answers for C1–C4 (3 attempts' worth each), C5–C10 placeholders at lower weight (2 each), and fatigue on. Brier **0.222** vs 0.216 for the v0.2 placeholder cards and 0.270 for the average. That's a statistical tie with v0.2 (+0.006, CI −0.001 to +0.013). Expected: your answers are deliberately wide, and my placeholders were written after seeing the labels. **Pantoja–Asakura:** 29% → **95%** → 94% (fatigue) → 83% (late two-on-one) → 100%; Air 100 → 4 at 18 s; Grip 100 → 46 (§4b).
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

### 2b. Defender AIR gauge (the health bar, an accumulator)
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
- [research/model/state_model.py](../research/model/state_model.py): finish model (fit, Laplace bands, leave-one-fight-out scores, calibration), the Air gauge (`health_trace`), and card weights from ranges (`card_weight`). Run: `C:/Users/netan/.venvs/ufc-cv/Scripts/python -I research/model/state_model.py [--priors <cards.csv>]`.
- [research/model/priors_placeholder.csv](../research/model/priors_placeholder.csv): 9 placeholder cards (8 positions + C10 fatigue). Your answers go into `priors_owner.csv` with the same columns, plus optional `p_low,p_high` or `bucket` (`<20`, `20-45`, `45-70`, `>70`). `USE_FATIGUE` in `state_model.py` switches the fatigue term on (runs M5); M6 = all cards as buckets.
- [research/model/priors_owner.csv](../research/model/priors_owner.csv): **the v0.3 cards MVP 0.2 should use** (your buckets C1–C4 + lower-weight placeholders C5–C10). [run_v03.py](../research/model/run_v03.py) reproduces §4b. For MVP 0.2: `sm.USE_FATIGUE = True; beta = sm.fit(other_fights_rows, cards("priors_owner.csv"))`; per frame `x = sm.x_at(row, t)` → `sm.predict(beta, x, sample=False)` and `sm.interval(...)`.
- [research/model/detector_events.py](../research/model/detector_events.py): event-level detector check (clip venv).
- [research/model/diagnose_mvp01.py](../research/model/diagnose_mvp01.py): reproduces the MVP 0.1 numbers.
- For `tools/mvp/demo.py` (Main): replace `fit`/`finish_prob` and the ramp with `state_model.fit` + `predict(..., sample=False)` (+ `interval` for the band); drive the defender bar with `health_trace` instead of `1 − finish %`; drive the attacker GRIP gauge from the same squeeze effort `G` (`100·e^(−G/12)`); snap to 100% / Air 0 at a finish frame and 0% at an escape; drop the 3-s post-event easing.
