# Coach review of the RNC finish model (v0.6 → v0.7 input)

2026-10-26 · coach-review session (an **AI-simulated** BJJ black belt / MMA grappling coach, not a real person). Reviewed: `research/priors_evidence/EVIDENCE.md`, `docs/MODEL_SPEC.md` §2 and §4e, `research/rnc_science/FACTORS.md`, the v0.6 weights, and the owner's comments.

**How to read the tags**
- 📘 **Consensus**: what most black belts and MMA grappling coaches teach; you'll hear it in any good back-attack class.
- 📚 **Citable**: an instructional, a fight, or a study you can look up. Fights are given so you can rewatch them; none has been labeled for this.
- 💬 **Opinion**: my judgment. Treat it like a low-confidence card (worth about 2 attempts, the same as the evidence cards C5–C9). It is **not** data.

Status colors: 🟢 agree · 🟡 partly agree / adjust · 🔴 disagree · ⚪ open

> ⚠ No study measures finish rates by RNC configuration (EVIDENCE.md says the same). Every multiplier below is 💬 opinion built on 📘 mechanics. The only 📚 number that bears on these weights is Stellpflug et al. (2020): once a choke is "fully locked", lock-to-out time doesn't differ by choke type (~9 s).

---

## Summary (one screen)

| Factor | v0.6 | Coach suggestion (80% range) | Verdict | Basis |
|---|---|---|---|---|
| Arm under the chin | ×4.0 (1.6–10.3) | **×4.0 (2.0–8.0)**; extra **×1.4** if the elbow is centered under the chin (`v_elbow`) vs the forearm blade on the throat | 🟢 keep, narrow it | 📘 + 💬 |
| Defender flattened | ×3.5 (1.2–10.4) | **×2.5 (1.2–5.0)** | 🟡 a bit high; it is soaking up some of the legs effect | 📘 + 💬 |
| Grip locked (all types lumped) | ×2.1 (0.9–5.3) | Split by grip: **figure-four ×2.6**, palm-to-palm / gable **×2.0**, wrist pull **×1.8**, short choke **×1.3** (each 0.8–4.5, shrunk toward one shared "locked" effect) | 🟡 split it, but less than the owner expects | 📘 + 📚 Stellpflug + 💬 |
| Choking hand tucked | ×1.7 (0.7–4.1) | **×1.25 (0.8–2.0)** main effect; its real job is to shrink the two-on-one effect (see that row) | 🟡 agree with the owner: smaller | 📘 + 💬 |
| Strong legs (BT or two hooks) | ×1.2 (0.5–2.5) | Split: **body triangle ×1.6 (0.9–3.0)**, two hooks **×1.3 (0.7–2.4)**. Most of the leg value is **retention and re-attacks**, which this per-attempt model can't see | 🟡 too low, and in the wrong place | 📘 + 💬 |
| Chin tucked | ×1.0 (0.4–2.2) | **×0.85 (0.5–1.3)** *given* the arm position. Its big effect happens *before* the arm gets under, and that's already counted by the arm factor | 🟢 near 1 is right; here's why | 📘 |
| Defender two-on-one | ×0.39 (0.17–0.92); keeps 25% of its effect once locked deep with the hand hidden | **×0.40 (0.2–0.8)**; keep **40%** of its effect (not 25%) once deep with the hand hidden; keep **70%** against palm-to-palm / gable / wrist pull | 🟡 direction right; the deep-lock discount is too generous | 📘 + 💬 (the labels lean the same way: 1/4 vs 10/14) |
| Attacker fatigue (full) | ×0.57 | **×0.6 (0.4–0.9)** | 🟢 | 📘 + 💬 |
| **NEW** re-attack (same position, within ~30 s) | none | **×1.3 per earlier attempt, cap 2 (0.8–2.0)** | ⚪ add | 💬 |
| **NEW** defender's hand inside the choke | none | **×0.35 (0.15–0.8)** | ⚪ add; high value | 📘 + 💬 |
| **NEW** defender's arm trapped | none | **×1.8 (1.0–3.5)** | ⚪ add | 📘 + 💬 |

**Gauge:** 🟢 9 s to out, 🟢 3-s blood recovery, 🟢 over the jaw 0.05 *for consciousness*. But 🔴 a locked arm over the jaw is a **crank**: it finishes by pain, not blood, so the finish % must not drop to ~0 there (keep C7 around 12–20%). 🟡 Chin-tuck relief: 0.30 → **0.15–0.20** once the arm is under. 🟢 Two-on-one relief 35% open; 🟡 10% when locked → **15%**.

**Sanity check (💬):** with my numbers, the "full house" (figure-four under the chin, flattened, hand hidden, body triangle, no defense) comes out near **85%**, which matches C5. C3 (locked under the chin + BT, two-on-one + tucked chin) comes out near **35%**, which matches the evidence and is below the owner's 45–70. A jaw grip with no lock against a defending opponent comes out near **4–8%**. The v0.6 multipliers chained together (×4 × 3.5 × 2.1 × 1.7 ≈ ×50) push the full house to the mid-90s, and in the UFC I don't believe that. The best back takers on earth still lose locked chokes to hand fighting, sweat, the cage and the bell.

---

## 1. Factor by factor

### 🟢 Arm under the chin (×4.0 → ×4.0, narrower range)
- 📘 **Mechanics:** a blood choke needs the two sides of the neck squeezed: the biceps on one carotid, the forearm on the other, with the trachea sitting in the crook of the elbow. That only happens when the chin is *above* the arm. Over the jaw, the mandible holds the forearm off the neck. 📚 Kesting (Grapplearts) and Danaher's back-attack material both treat "get under the chin" as the whole game.
- 💬 **Owner says "super important, obviously": agreed.** I'd narrow the range: the lower bound of 1.6 is too timid for the single most important variable in the choke.
- 💬 **What the label misses:** "under the chin" covers two very different chokes.
  - **Elbow centered under the chin (`v_elbow`)**: a true strangle, ~9 s to out.
  - **Forearm blade across the throat**: mostly a windpipe/air choke. It hurts, it's slower, and people survive it longer.
  The code book already has `forearm_placement`. Promote it: **×1.4 for `v_elbow` over `blade`**, given the arm is under.

### 🟡 Defender flattened (×3.5 → ×2.5)
- 📘 **Why flattening matters:** once the defender's back is flat on the attacker's chest and hips are stretched out, he can't (a) turn in, (b) slide his shoulders to the mat on the choking-arm side (the standard escape), or (c) post to stand. The attacker can also arch and "stretch" him, which lengthens the neck and lifts the chin. 📚 Marcelo Garcia's back game and Danaher's "Back Attacks: Enter the System" (BJJ Fanatics) both teach flatten-then-finish.
- 💬 **Owner: "flattened usually means a better position, getting in deeper": agreed,** and that's exactly the problem: flattened is partly a **marker** of depth rather than a separate cause. It co-occurs with the body triangle (you flatten *with* the triangle) and with a deep arm. With ~35 attempts the model can't separate them, so flattened is likely taking credit that belongs to the legs (and the legs factor reads ~1.2 as a result).
- 💬 Suggest **×2.5 (1.2–5.0)** and raise the body triangle (below). Labels: flattened 6/6 when under + locked. Six for six is a tiny sample.

### 🟡 Grip type (one ×2.1 → split, modestly)
- 📘 **Figure-four (mata leão):** the choking hand grips the opposite biceps, and the back hand goes behind the head and pushes it forward into the V. Two strengths: (1) the loop closes around the neck *and* the head is driven into it, so it's very deep; (2) the choking hand is buried on the biceps and the defender can't grab it. **Its edge is security: it's hard to break.**
- 📘 **Palm-to-palm / gable:** both hands are in front of the neck. You can pull straight back with both arms, and that squeeze is very strong. The weakness is that both hands are exposed, so a two-on-one or a wrist peel has something to grab. Used when the head is defended or the back hand can't get behind the head.
- 📘 **Wrist pull ("Dagestani" style):** the second hand pulls the choking wrist across. Strong in scrambles and from body locks; often a stepping stone into palm-to-palm or figure-four. No head push.
- 📘 **Short choke:** the arm only partly across, with the blade on the throat. A pain/air choke. It finishes, but slowly.
- 📚 **Stellpflug 2020:** once *fully locked*, lock-to-out time doesn't differ by choke type. So the owner's "figure-four is way stronger and deadlier" is 🟡 **half right**. It's not that the squeeze is faster. It's that **the lock survives the defense** more often.
- 💬 **My split** (offsets from no lock, all shrunk toward one shared "locked" effect so the small groups don't run wild): figure-four ×2.6, palm-to-palm / gable ×2.0, wrist pull ×1.8, short choke ×1.3. The figure-four vs palm-to-palm gap (~×1.3) is real but modest. **The bigger difference shows up as an interaction**: the two-on-one hurts a palm-to-palm a lot more than a buried figure-four (see the two-on-one row). If v0.7 can only afford one change here, model the interaction, not four main effects.
- 💬 **Owner's "without a lock it's very hard": agreed** for finishing. One-arm chokes do finish (labels 4/8), but mostly against a defender who's already hurt or flattened.

### 🟡 Choking hand tucked (×1.7 → ×1.25)
- 📘 This is really a sub-feature of the figure-four: the fingers disappear behind the biceps (or behind the shoulder in a palm-to-palm variant), so the defender can't peel the hand.
- 💬 **Owner is right:** it only matters when the defender is attacking that hand. If his hands are on the back hand, or he's posting, or he's hurt, tucking changes nothing. So: a **small main effect (×1.25)**, and make it **switch off most of the two-on-one effect** instead. That's what "depends on where the defender's hands are" means in model terms.

### 🟡 Strong legs (×1.2 → body triangle ×1.6, hooks ×1.3, plus retention)
- 📘 **Why the body triangle beats hooks in MMA:**
  1. **It can't be stripped.** The standard escape is to kick off the bottom hook and slide your shoulders to the mat on that side. A locked triangle has no hook to clear.
  2. **It squeezes the diaphragm.** He breathes worse, and his hands get tired from fighting yours.
  3. **It lets you flatten and stretch** (see flattened).
  4. **It holds through strikes, sweat, the cage and the bell.** Hooks get kicked off and slip with sweat. 📚 Demian Maia is the reference: body triangle, then a patient hand fight, then the choke (e.g. Maia vs Carlos Condit, UFC on Fox 21, 2016, RNC in round 1).
  - **Downside:** lock the triangle with the wrong ankle on top and the defender can fall toward the short side and come up. Hooks are better for adjusting and re-taking the back in a scramble.
- 💬 **Owner: "super important, especially for re-attacks": agreed, and this explains the flat labels.** Most of the triangle's value isn't "this attempt finishes"; it's "**he can't escape, so I get attempt #2, #3, #4**." A per-attempt finish model scores each failed attempt as a failure and never credits the legs for buying the next one. Labels BT 6/15 vs hooks 5/10 is exactly what you'd expect.
- 💬 **What I'd do:** (a) split BT ×1.6 and hooks ×1.3 in the per-attempt model; (b) add a **re-attack factor** (below); (c) later, when "P(he finishes in this back exposure)" matters, model the exposure as a chain where the legs reduce the escape hazard. That's for after v0.7.

### 🟢 Chin tucked (×1.0 → ×0.85, given the arm position)
- 📘 **Before the arm is under:** the chin tuck is the *first* line of defense. It keeps the forearm on the jaw. So it matters a lot, but its effect flows **through** the arm variable (tucked chin → arm stays on the jaw → low finish %). Because the model already conditions on arm position, the chin tuck's *extra* effect is small. That's why the model reads ~1.0, and it isn't a bug.
- 📘 **After the arm is under:** a tucked chin squeezes down on the forearm and can keep the elbow from sliding all the way through. That makes it a blade choke instead of a V. It also buys a second or two. It's a small effect.
- 💬 **Owner: "once the arm is under, I don't know."** My answer: it's small, ×0.85. Lower the gauge's chin relief from 0.30 to **0.15–0.20** under the chin. If you want the chin tuck to "count", model it as slowing the **jaw → under-the-chin transition**, not as a finish multiplier.

### 🟡 Defender two-on-one (×0.39 → ×0.40; deep-lock keep 25% → 40%)
- 📘 **When it works:** before the lock, both hands on the choking wrist, pulling it down and away from the neck (*glued to the wrist*). This is the textbook defense, and it's very effective. 📚 Back-escape instructionals (Lachlan Giles' back escape material, Saulo Ribeiro's *Jiu-Jitsu University*) start here.
- 📘 **After the lock**, the two-on-one changes its target: against a figure-four he peels the **back hand** off his head; against a palm-to-palm he can attack the clasp directly. Peeling a buried figure-four is hard but not hopeless, especially when the attacker is tired or sweaty.
- 💬 **Owner: "the two-on-one does help": agreed.** But keeping only 25% of the effect after a deep lock is too optimistic for the attacker. The labels lean the other way too (under + locked: 1/4 with a two-on-one vs 10/14 without). I'd keep **40%** for a deep figure-four with the hand hidden, and **70%** against palm-to-palm / gable / wrist pull.
- 💬 **"Reaching for the other hand is hard to measure": true.** A simple code is enough: **which hand** the two hands are on (`choking_wrist` / `back_hand` / `split` / `none`).

### 🟢 Attacker fatigue (×0.57 → ×0.6)
- 📘 Forearms burn out fast on a squeeze that isn't finishing. Coaches say to switch grips or reset rather than "squeeze harder". The defender tires too (hand fighting, the triangle on his diaphragm), which partly cancels it. Keep it data-driven.

### 🔴 → 🟢 "Over the jaw barely chokes" (gauge 0.05): right for blood, wrong for finishes
- 📘 A forearm on the jaw doesn't block the carotids, so **0.05 for the consciousness gauge is right.**
- 📘📚 **But it still finishes fights by pain**: the forearm across the mouth or jaw cranks the neck and the teeth. 📚 Khamzat Chimaev vs Robert Whittaker (UFC 308, 2024, face crank, round 1); Khabib Nurmagomedov vs Conor McGregor (UFC 229, 2018, recorded as a neck crank). Pressure on the jaw also makes defenders lift the chin, and then the arm slides under (📚 Kesting).
- 💬 **So:** keep the gauge at 0.05, but **don't let finish % collapse** for a *locked, squeezing* jaw grip. Keep C7 at **12–20%**. It also helps to give the jaw state some chance of turning into "under the chin" within a few seconds.
- 💬 **Labeling payoff:** tag *how* a jaw finish ended (instant tap with a hand at the mouth or face = crank). Then the gauge isn't blamed for a pain tap.

---

## 2. Suggested numbers for model-expert (v0.7)

All 💬 opinion unless marked. Weight them like the evidence cards (**n0 ≈ 2**). I read the same labels (only to sanity-check direction), so don't weight them more than that.

| Term | Multiplier (odds) | 80% range | Type |
|---|---|---|---|
| arm under the chin | 4.0 | 2.0–8.0 | 💬 + 📘 strong consensus |
| `v_elbow` vs `blade` (given under) | 1.4 | 0.9–2.2 | 💬 |
| flattened | 2.5 | 1.2–5.0 | 💬 |
| figure-four (vs no lock) | 2.6 | 1.1–5.5 | 💬 (📚 Stellpflug limits the gap between grips) |
| palm-to-palm / gable | 2.0 | 0.9–4.5 | 💬 |
| wrist pull | 1.8 | 0.8–4.0 | 💬 |
| short choke | 1.3 | 0.6–2.8 | 💬 |
| choking hand tucked | 1.25 | 0.8–2.0 | 💬 (agrees with the owner) |
| body triangle | 1.6 | 0.9–3.0 | 💬 |
| two hooks | 1.3 | 0.7–2.4 | 💬 |
| chin tucked (given arm position) | 0.85 | 0.5–1.3 | 💬 + 📘 |
| two-on-one | 0.40 | 0.2–0.8 | 💬 + 📘 strong consensus |
| …effect kept: deep figure-four + hand hidden | 40% | 25–60% | 💬 |
| …effect kept: palm-to-palm / gable / wrist pull | 70% | 50–90% | 💬 |
| attacker fatigue (full) | 0.6 | 0.4–0.9 | 💬 |
| re-attack (per earlier attempt, same back exposure, < 30 s apart, cap 2) | 1.3 | 0.8–2.0 | 💬 |
| defender's hand inside the choke | 0.35 | 0.15–0.8 | 💬 + 📘 |
| defender's arm trapped | 1.8 | 1.0–3.5 | 💬 + 📘 |
| defender hurt before the back take (knockdown or clearly rocked) | 2.0 | 1.0–4.0 | 💬 |

**Gauge:** secs_to_out 9 (📚), blood recovery 3 s (📚), jaw squeeze 0.05 (📘), chin relief **0.15–0.20** under the chin (💬), two-on-one relief 35% open / **15%** locked (💬), lingering 20% over 60 s (📚 low confidence, fine).

**Re-attacks (owner's Oliveira point) 💬:** I agree a second attempt should read *higher*, for three reasons: his forearms are spent from the hand fight, there's residual ischemia, and the attacker has read his defense. Two things pull the other way: he survived once, so he may be a good defender, and the attacker is tired too. In my experience the net effect is positive **when the attacker kept the back** and the next attempt comes within ~30 s. After a scramble or a long gap, treat it as a fresh attempt. So: tie the bonus to *same back exposure* + *short gap*, and let it **stack with** the blood-recovery and lingering terms rather than replace them.

---

## 3. What the model is missing

Importance: 🔴 high · 🟡 medium · ⚪ low. "Labelable" = from a broadcast at normal speed: **easy / medium / hard**.

| Factor | What to watch | Importance | Labelable | Note |
|---|---|---|---|---|
| **Defender's hand inside the choke** | A defender hand (or glove) trapped between the forearm and the neck | 🔴 | easy–medium | A hand inside usually kills the strangle (the attacker must switch to a crank or reset). The best "no" signal I know of. |
| **Defender's hand position** | Glued to the choking wrist / on the back hand / hand behind his own head / posting or striking / none | 🔴 | medium | Extends `defender_two_on_one` to *where* the hands are. "Hand behind the head" blocks the figure-four's back hand. |
| **Re-attack count + gap** | Attempt #k in the same back exposure, seconds since the last one ended | 🔴 | easy (derived from labels already logged) | Owner's Oliveira point. Costs nothing to compute. |
| **Defender's arm trapped** | One defender arm pinned by the attacker's leg (leg over the arm) or arm | 🔴 | medium | No two-on-one possible → big swing. Common in Maia- and Dagestani-style backs. |
| **Elbow alignment** | Elbow centered under the chin (V) vs blade across | 🔴 | medium–hard (angle-dependent) | Already in the code book as `forearm_placement`; promote it. |
| **Defender hurt before the back take** | A knockdown or clear wobble in the ~10 s before | 🔴 | easy | Many UFC RNCs follow a knockdown. Without it the model credits position for what damage did. |
| **Defender's escape direction** | Shoulders sliding to the mat on the choking-arm side (classic escape) vs turning in vs sitting up | 🟡 | medium | `defender_turning` is excluded as part of the escape definition. Code *early* movement at L, before it becomes the escape. |
| **Cage proximity** | Defender can reach the fence to wall-walk / stand; attacker's back on the fence (can't stretch) | 🟡 | easy | MMA-specific. Fence = a stand-up escape route. |
| **Seatbelt before the choke** | Seatbelt established before the arm goes across vs the arm shot straight in from a scramble | 🟡 | medium | Already `upper_body`. A seatbelt-first choke is usually deeper. |
| **Back context** | Ground back / turtle ride / standing back | 🟡 | easy | Already coded. Standing back chokes finish less unless the body lock drags him down. |
| **Round time left** | Seconds to the bell | 🟡 | easy | Already primary. Defenders also *stall to the bell*, so the last ~20 s favors survival. |
| **Attacker's head position** | Attacker's head tight to the defender's head on the choking side ("ear to ear") vs drifting | ⚪ | hard | Coaches watch it; broadcast rarely shows it. |
| **Squeeze mechanics** | Elbows pulled back, chest expanded, wrist rotation | ⚪ | hard | Visible as "fading" more reliably than as technique. |
| **Sweat / late round** | Slippery grips, gloves | ⚪ | hard | Round number is a weak proxy. |

**Best value for v0.7 (💬):** re-attack count (free), hand inside the choke, defender hurt before, arm trapped. Three of the four are easy or medium to label.

---

## 4. Notes for the owner while labeling

1. 🔴 **Code at L = 2 s, then don't look again.** Pause and code before you know the ending. Knowing the outcome shifts "under the chin" and "flattened" toward finishes. It happens to everyone, coaches included.
2. 🟡 **Arm under the chin = the elbow crook under the chin and the chin above the forearm.** Chin resting on the forearm with the forearm on the throat = under, `blade`. Forearm touching the mouth, nose or jawline = `over_jaw`. If you can't see it, mark it unclear.
3. 🟡 **Flattened = his shoulder blades on your chest/the mat, hips stretched out, not able to turn.** Sitting up or on his side ≠ flattened, even if the choke is deep.
4. 🟡 **Grip:** log the first grip you clearly see at L, and the sequence after. Figure-four needs the choking hand **on the biceps** *and* the other hand behind the head. A hand on the traps = `second_hand_on_traps`, not figure-four.
5. 🟡 **Hand tucked = you can't see the choking fingers** (buried behind the biceps or shoulder). If the defender can touch them, it isn't tucked.
6. 🟡 **Two-on-one: note what the hands are on**: choking wrist, back hand, or split. One hand on the wrist and one posting is *not* a two-on-one.
7. ⚪ **New quick tags (if you're willing):** `hand_inside`, `arm_trapped`, `hurt_before`, `near_cage`. Each is yes/no, about two seconds per attempt.
8. ⚪ **How did a finish end?** Instant tap with a hand at the face or jaw = **crank (pain)**. Slow fade, arms dropping, late tap or unconscious = **blood**. That's one more outcome tag, and it fixes the jaw-gauge confusion.
9. ⚪ **Re-attacks:** if an attempt starts within ~30 s of the last one ended *and he never got off the back*, note "same exposure". The model can then count re-attacks.
10. ⚪ **When in doubt, mark unclear.** An honest unclear helps the model more than a guess. The 💬 numbers above can be wrong; your labels are the only thing that can prove it.

---

### Sources mentioned
- 📚 Stellpflug et al. (2020), *Int J Perf Anal Sport* 20(4):720–728 (9 s lock-to-out; no difference by choke type). Cited fully in `EVIDENCE.md`.
- 📚 Stephen Kesting, Grapplearts on the RNC over the jaw (link in `EVIDENCE.md`).
- 📚 John Danaher, *Back Attacks: Enter the System* (BJJ Fanatics instructional).
- 📚 Marcelo Garcia, *Advanced Jiu-Jitsu* (Victory Belt, 2008), back-control chapters.
- 📚 Saulo Ribeiro, *Jiu-Jitsu University* (Victory Belt, 2008), back survival/escapes; Lachlan Giles' back escape material (BJJ Fanatics). Exact title not verified.
- 📚 Fights to rewatch: Maia vs Condit (2016, RNC with body triangle); Chimaev vs Whittaker (UFC 308, face crank); Khabib vs McGregor (UFC 229, neck crank); Pantoja vs Asakura (in the repo, the model's reference clip).
- No study gives configuration effects; every multiplier here is 💬 opinion.
