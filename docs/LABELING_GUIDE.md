# RNCV labeling guide

Everything you need to label, in one place. The tool is [tools/labeler/index.html](../tools/labeler/index.html) (open it in **Chrome**). Field definitions come from the code book [research/rnc_science/FACTORS.md](../research/rnc_science/FACTORS.md); if the two ever disagree, FACTORS.md wins. **Picture version:** [rnc_codebook.html](rnc_codebook.html) (open in Chrome; one card with a drawing per option, for the 12 freeze-frame questions; it predates `upper_body`, which is described in section 4 below).

---

## 1. Each sitting (2 min)

1. Open `tools\labeler\index.html` in Chrome and press **Ctrl+Shift+R** (gets the newest version).
2. **Load fight list(s) CSV** → in `phase3_labels\`, hold Ctrl and pick `labeling_queue_successes.csv`, `labeling_queue_failures.csv`, `random_10.csv`.
3. **Load labels.csv** → pick `phase3_labels\labels.csv` (syncs the browser with the latest file).
4. **Link labels.csv file** → pick the same `phase3_labels\labels.csv`. The header must now say **linked: labels.csv**. Every save is written straight to the file. (It refuses to link a queue file, on purpose.)
5. Close `labels.csv` in Excel while you label (Excel locks the file).

## 2. Each fight (1 min)

1. **Fight** drop-down → pick the fight (attacker vs defender, queue rank).
2. Attacker = the one choking. Wrong way round → **W**.
3. **Open video** → your clip in `data\clips\`.
4. **Clock:**
   - **Finish fights** (from the successes queue): skip the clock. When you save the finishing attempt, the tool anchors the round clock to the official finish time and back-fills earlier attempts in the clip.
   - **Failure rounds:** pause where the on-screen round clock is readable → **C** → type the time **remaining** (e.g. `3:12`) → Enter.
   - **Compilation / highlight clips** (clock unreliable): write `compilation` in notes.

## 3. Each attempt (~2 min)

| When | Do | Keys |
|---|---|---|
| Choke starts: attacker on the back, arm across the neck, second hand working to lock | Pause on that frame | Space, **S** |
| Tool freezes ~2 s later (blind: you haven't seen the end) | Code what you see **in the frozen frame**: number per field, ↑/↓ to move, Enter. Can't see a field → leave blank. Whole view blocked (ref, cut, angle) → **X** | 1–9, ↑↓, Enter / **X** |
| Something changes during the attempt (body lock added, hooks, arm slides under chin, two-on-one, grip, side switch…) | **G** → every field shows its current value highlighted → press a number only where it changed → Enter | **G** |
| The end (tap, ref stop, goes limp, escape, position change, bell) | Pause on that frame | Space, **E** |
| Outcome panel | Pick outcome, Enter. Mistake on the last row → **U** | numbers, Enter |

Other keys: ←/→ 1 s (Shift = 5 s) · `,` `.` one frame · `[` `]` speed · **B** back 10 s · **T** + number = add grip to the style sequence.

**Round watched, no RNC at all?** Don't make a row. Tell Main "rank N watched, no RNC" (it's recorded as a real negative).

---

## 4. How to judge each field (at the 2-second freeze)

Rule for every field: **judge only what you can see in that frame. Blank = not visible. Never guess.** "unclear" means you can see the area but can't decide.

### Main (pre-registered) fields: these matter most

| Field | Options | How to judge |
|---|---|---|
| **choke_arm_position** | `under_chin` · `over_jaw` · `unclear` | Where is the choking forearm/biceps? **under_chin** = the arm is below the jaw line, against the throat/neck. **over_jaw** = the chin is tucked and the arm sits on the jaw or face. |
| **control** (legs) | `two_hooks` · `body_triangle` · `one_hook` · `none` | **two_hooks** = both of the attacker's heels inside the defender's thighs. **body_triangle** = legs locked in a figure-four around the waist. **one_hook** = only one heel in. **none** = no legs in (standing, turtle ride with no hooks). |
| **defender_two_on_one** | True · False | True = **both** of the defender's hands are on the choking arm (pulling it down / off). One hand, or hands elsewhere = False. |

### Grip and arm details (exploratory)

| Field | Options | How to judge |
|---|---|---|
| **rnc_style_at_L** | `figure_four` · `palm_to_palm` · `gable` · `wrist_pull` · `short_choke` · `one_arm` · `unclear` | **figure_four** = choking hand on the opposite biceps, other hand behind the head (classic). **palm_to_palm** = hands clasped palm to palm. **gable** = thumbless clasp (gable / S-grip). **wrist_pull** = "Dagestani": second hand grabs the choking wrist/forearm and pulls, no hand behind the head. **short_choke** = arm only partly across, blade of the forearm on the throat, hand ends at own shoulder. **one_arm** = second hand not involved. |
| **forearm_placement** | `blade` · `v_elbow` · `across_jaw` · `unclear` | **blade** = the bony edge of the forearm presses the throat. **v_elbow** = elbow centered under the chin, biceps and forearm on the two sides of the neck (a "V"). **across_jaw** = forearm on the jaw line. |
| **choking_hand_tucked** | True · False | True = the choking hand is hidden deep (on the opposite biceps or shoulder), not just gripping. *Definition being confirmed by your research.* |
| **second_hand_on_traps** | True · False | True = the non-choking hand is on the defender's trapezius/shoulder instead of behind the head. |
| **squeeze_direction** | `straight_back` · `tilt_choke_side` · `tilt_away` · `pull_up` · `unclear` | Which way the attacker is finishing: arching straight back, tilting the head toward the choking-arm side, tilting away, or pulling up. Often hard to see: use `unclear` freely. |
| **attacker_side** | `left` · `right` | Which arm is the choking arm (attacker's left or right). |

### Defender and position (exploratory)

| Field | Options | How to judge |
|---|---|---|
| **chin_tucked** | True · False | True = the defender's chin is down, blocking the neck. |
| **opponent_flattened** | True · False | True = the defender is flat on their stomach (or flat on the back of the attacker), so they can't turn in. |
| **back_context** | `ground_back` · `turtle_ride` · `standing_back` · `scramble` | **ground_back** = classic back mount on the mat (either fighter on top). **turtle_ride** = defender on knees/turtle, attacker riding on top. **standing_back** = both standing, attacker on the back. **scramble** = mid-transition, no settled position. |
| **upper_body** (G panel only) | `body_lock` · `seatbelt` · `none` | **body_lock** = arms locked around the torso. **seatbelt** = one arm over the shoulder, one under the armpit, hands joined. Separate from legs (`control`). |

### Outcome (end panel)

| Outcome | When |
|---|---|
| `tap` | Physical or verbal tap |
| `ref_stop` | Referee stops it (defender not tapping, not limp) |
| `unconscious` | Defender goes limp (end = first limp frame) |
| `escape` | **Defender** gets out: arm off the neck **and** back control lost, or turns in to face the attacker |
| `position_change` | **Attacker** abandons the choke (goes to mount, armbar, etc.), or the position reverses while the choke is off |
| `bell` | Round ends with the choke still on. Kept, but the analysis treats it as "unknown ending" |

---

## 5. Notes tokens

Type these in **notes** when they apply: `pilot` (first 15 attempts; Main adds it), `compilation` (unreliable clock). The tool adds `no_clock` / `clock=finish_anchor` itself.

## 6. Rules

- One sitting = 3–5 clips (15–20 min).
- Men's fights only (PREREG A1). Skip rows with status `out_of_scope_womens`.
- Clips stay on your laptop. Never upload them.
- Unsure about a rule → ask Main or the secretary; don't invent one.
