# RNCV code tour, file by file (source for a NotebookLM audio overview)

Status date: 2026-10-28. Written for the project's owner: a BJJ practitioner who isn't a programmer or statistician. The goal is to walk through the code in the order data flows through it. For each file: what it does, the one idea behind it, a real number from the project, and the story of what went wrong or what was learned there. Everything here is true to the project today, including what doesn't work.

**Suggested NotebookLM "customize" prompt:** *"Two hosts give a 12-minute code tour of this project for its creator, who knows jiu-jitsu but not programming. Go file by file in the order the data flows: labeler, labels, detector, finish model, overlay, neck crops, analysis. For each file explain what it does in plain words, one key idea, one real number, and one story of what went wrong. Use BJJ analogies. Be honest about weak results. No jargon without a one-line explanation."*

---

## The big picture in one paragraph

The project turns UFC choke footage into three things: a **labeled dataset** (the owner watches fights and records each rear-naked choke attempt and its details), **models** (an attempt detector that looks at the video itself, and a finish model that turns a choke's position into a finish chance and the defender's HP), and a **replay overlay** that shows it all on screen. The data flows like a scramble to the back: first you find the attempt, then you read the position, then you judge whether it finishes. Every file below is one step of that chain. Footage never leaves the laptop: only labels, numbers and code go to GitHub.

---

## Stop 1: `tools/labeler/index.html`, where every data point is born

**What it does:** a single web page that runs in Chrome, with no server. You open a fight video, press **S** when a choke attempt starts and **E** when it ends. Two seconds after S, the video pauses itself and asks a fixed set of questions: where is the choking arm (under the chin or over the jaw), what's the grip (figure-four, palm-to-palm, wrist pull, one arm), what are the legs doing (body triangle, both hooks, one hook), is the defender two-on-one hand fighting, is the chin tucked. Press **G** whenever the position changes mid-choke, for example when the grip switches to a figure-four. Then you record the outcome: tap, unconscious, escape, position change or bell.

**The key idea: blinding.** The questions come at a fixed moment, 2 seconds in, before you see how the choke ends. Otherwise you'd unconsciously describe finished chokes as "tighter". This "landmark" idea comes straight from the pre-registration.

**The clock trick:** UFC broadcasts don't show the round clock all the time. So when the fight list knows the official finish time (from ufcstats), the labeler anchors the whole clip's clock to the tap. Every earlier attempt in that round gets its round time back-filled automatically.

**Stories:**
- **Stale rows.** The labeler keeps a copy of rows in the browser. More than once, an old browser copy wrote deleted or wrong rows back into the file: a deleted Elkins row, a women's fight, a Tybura row saved under the wrong fight. The fix grew in three steps:
  1. re-read the file before every save;
  2. a link prompt that lists old rows and recommends Cancel;
  3. most recently, a rule that if someone edited the file outside the tab, the file wins for every row the tab saved before that edit.
- **Wrong fight selected.** Twice, a new video was labeled while the previous fight was still selected. Now there's a search box: type "allen muniz" or "#12" and the fight is picked.

## Stop 2: `phase3_labels/labels.csv` and `qa_labels.py`, the dataset and its referee

**What it is:** one row per choke attempt, about 35 columns. Today: **73 attempts from 42 UFC fights**, men's divisions only.

**`qa_labels.py`** is the quality check. It flags overlapping attempts in the same round, round times outside 0–300 seconds, a finish whose end doesn't match the official finish time, fights out of scope (women's bouts, by amendment A1), and fighters over the cap (at most 5 attacking rounds, amendment A4). Red rows must be fixed before any analysis.

**Story:** Ulberg vs Jung was labeled "bell" because the choke ran to the horn, but he was officially awarded the submission. QA caught the 300.1-second end time, and the row became a tap with a note explaining why.

## Stop 3: `tools/fetch_clips.py` and `tools/cleanup_clips.py`, the supply line

**fetch_clips** walks the list of 254 findable RNC finishes, searches YouTube and downloads only official UFC uploads at 720p into `data/clips/to_label/`. It skips women's bouts, pre-2018 fights and capped fighters. **The lesson behind it:** hand-picked links included a video-game render (EA UFC), an Allen highlight compilation and a fan channel calling itself "Ufc". So now there's a channel whitelist, a list of banned title words (highlights, interview, countdown, best of) and a blocklist. Official uploads are nearly used up: 18 of 254 so far. A `--failures` mode fetches rounds where a choke failed, which matter most now.

**cleanup_clips** deletes a labeled video only when both its detector features and its neck pictures are saved, and never while labeling is active (labels saved in the last 30 minutes). **About 1.8 GB** of used clips were freed in one night.

## Stop 4: `research/attempt_clf/attempt_clf.py`, turning video into numbers the detector can use

**What it does:** samples 2 frames per second, crops each frame to the fighters, and runs each crop through **CLIP**, a big public image model that turns any picture into a list of 512 numbers, a kind of fingerprint of what's in the picture. No pose skeletons are involved.

**Why not skeletons?** An early pose review found that both fighters' skeletons were right in only **4 of 48** tangled frames. In a back take, arms and legs belong to the wrong person half the time. So the detector looks at the whole picture instead.

**Stories:**
- **The video clock bug.** Some `.webm` downloads have a variable frame rate. Counting frames ÷ 30 drifted up to **9.9 seconds** from the real time. That's why the demo's overlay once came up late. Everything now reads the real timestamp of each frame.
- **Only the part you watched.** Full-fight videos include walkouts and other rounds where nobody labeled anything, and there might be unlabeled chokes there. So the detector only uses the stretch from 2 minutes before your first labeled attempt to 30 seconds after the last.
- **Features are saved per clip**, so a relabel never forces re-processing a video. That's why videos can be deleted afterwards.

## Stop 5: `research/attempt_clf/detector_v2.py`, the attempt detector

**What it does:** a simple **logistic regression** (a weighted vote over those 512 numbers) learns "inside a choke attempt or not". Version 2 also looks at the average picture of the last 2 and 4 seconds, so it sees movement ("the arm comes across"), not just a still photo.

**How it's tested:** leave-one-fight-out. For every fight, the model is trained on all the other fights and scored on that one. That's the honest test: the model never sees the fight it's judged on.

**The numbers, honestly:** frame ROC-AUC climbed **0.70 → 0.80** as fights were added, then settled at **~0.75** on 40 fights once far more no-choke footage came in. (ROC-AUC: 0.5 is guessing, 1.0 is perfect.) It's good at "a back attack is happening". It's bad at the exact second a choke starts (right within 2 seconds only ~9% of the time) and fires 0.7–1.0 false alarms per minute of grappling.

**Tried and rejected** (all written up in `reports/attempt_detector_v2.md`): a separate "choke is starting" model (ROC-AUC 0.56), and crops around the heads (no better). Conclusion: limited by data, not by the design.

## Stop 6: `research/model/state_model.py`, the heart of the finish model and the HP meter

**The finish model's idea:** the chance this choke finishes, *given what's visible right now*. Each factor multiplies the odds. It's a logistic model, the same kind of weighted vote as the detector, but over BJJ factors instead of pixels.

**Where the knowledge comes from:** "scenario cards". The owner answered questions like "figure-four under the chin, body triangle, no hand fighting: how often does that finish?" with buckets (under 20%, 20–45%, 45–70%, over 70%). Each answer counts as about 3 pretend attempts. A published-evidence review added more cards. Then the real labels pull the numbers toward what UFC fights actually show. With few labels the cards matter; as labels grow, the data takes over.

**The HP meter** (`consciousness_trace`): a blood-flow model, not a forecast. Each position has a squeeze strength: a locked figure-four under the chin with the hand hidden is about 0.9, one arm about 0.45, over the jaw 0.05. At full squeeze, HP runs out in **9 seconds**: the average from lock to unconsciousness in 81 MMA choke-outs (Stellpflug 2020). HP refills about 3 seconds after air comes back, and part of the fatigue lingers for re-attacks. The labels later showed finishes took a **median 9.6 seconds** on the neck, a nice independent match.

**Story:** the very first version (MVP 0.1) multiplied everything by a time ramp, so a locked figure-four read **2%** and a knockout read 30%. The owner rejected it, and the whole model was redesigned around "the position right now" with no time ramp.

## Stop 7: `model_v07.py`, `run_v07_coach.py`, `explore_v08.py`, the model versions

**v0.7** split the factors the way a coach would: figure-four vs other locks vs one arm, body triangle vs hooks, and a smaller "hand hidden" effect that mainly cancels the defender's two-on-one.

**v0.7c** added the **BJJ coach review**, an AI coach agent's multipliers, used as the starting point for each factor (arm under the chin ×4, figure-four ×2.6). Honest note: that's AI opinion, weighted lightly.

**v0.8**, today's model: `explore_v08.py` tested six principled variants and logged every one: a re-attack term, time left in the round, tighter or looser coach priors, and a leaner model. The **leaner one won**: drop the factors the data can't pin down yet (both hooks, chin tucked). Brier score (prediction error; lower is better) 0.245 vs 0.249.

**The honest bottom line:** from the 2-second snapshot alone, the model barely beats "always guess the average" (0.245 vs 0.254, within noise). Following the position as it changes, it clearly does better (0.224 vs 0.254). **The value is in tracking how the choke develops.**

## Stop 8: `findings.py`, `charts.py`, `prereg_analysis.py`, the science

**findings.py** writes `reports/findings_pilot.md`: plain finish rates per factor with honest 95% intervals.
- Hidden hand: 75% finished vs 48%. Flattened: 66% vs 49%.
- Body triangle (46%) finished *less* than one hook or none (68%) per attempt. The likely reason: leg control buys more attempts and more time on the back, and the early attempts fail. Also, hurt defenders get choked before any hooks are in.

All of this is labeled **exploratory**.

**charts.py** draws the two README charts. The **effects chart** shows each factor's multiplier with its range: arm under the chin ×5, flattened ×3, figure-four ×2.4, two-on-one ×0.5. The **calibration chart** asks: when the model says 80%, does it finish about 80% of the time? At the top end, yes. At the low end, the model is too pessimistic.

**prereg_analysis.py** is the frozen, pre-registered test, written before the data exists. It tests three hypotheses: arm under the chin helps, strong legs help, the two-on-one hurts. It uses Firth logistic regression and labels each result supported, contradicted or inconclusive. It refuses to run on real data before ~150 attempts. Tested on simulated data, it showed something sobering: at 150 attempts, a ×2 effect is only detected **42%** of the time. Medium effects need more data or will honestly come out "inconclusive".

## Stop 9: the overlay, `tools/mvp/demo.py`, `tracking.py`, `hud.py`, `detector_live.py`

**demo.py** plays a labeled clip and draws everything. On the left is the video. On the right is the side tab:
- the real detector's status ("SCANNING", then "BACK ATTACK DETECTED"; trained without this fight);
- the attacker's finish chance;
- the defender's HP with an estimate of the seconds of air left;
- big factor boxes colored by the model's own weights: gold = very helpful, purple = helpful, blue = small, red = against.

They pop in with a shock ring when the position changes.

**tracking.py** draws on the fighters:
1. Quiet corner brackets.
2. Stick figures, shown only as brief flashes when a pose is steady and anatomically plausible. The pose model claimed 97% confidence even on garbage skeletons, so steadiness is measured instead.
3. A reticle that locks onto the neck when the choke starts and stays put.
4. The referee is filtered out by clothing color: black shirt and pants vs bare skin.

**Stories:**
- **Owner feedback reshaped it repeatedly:** "the stick figures look like voodoo", "the reticle keeps turning on and off", "HP drained before the arm was in". The last one led to a 2-second "setting the choke" ramp.
- **A fresh-eyes product reviewer** pushed "one home per number" and the ending card ("TAP · CHARLES OLIVEIRA WINS · 24 s on the neck").

## Stop 10: `tools/save_neck_crops.py` and `factor_neck.py`, teaching the computer to see the factors

**The problem:** the factors (arm under the chin, figure-four…) still come from the owner's labels. A pilot (`factor_pilot.py`) asked whether the detector's whole-picture fingerprints can see them. Answer: **no**. Agreement with the owner's labels was near zero (κ ≤ 0.17, target 0.4). The picture is too wide and the hands are too small.

**The plan:** `save_neck_crops.py` saves small zoomed pictures of just the head and neck area, 4 per second, for every labeled attempt, before the video is deleted. `factor_neck.py` learns the factors from those, with the same leave-one-fight-out test. It runs end to end on 15 fights so far, too few to tell. The real decision comes at ~150 attempts. These pictures are UFC pixels, so they stay on the laptop.

## Stop 11: `tools/release_check.py`, the gatekeeper for going public

Before the repo goes public, this scans every file and the whole git history for video files, passwords and keys, personal computer paths and internal files. Today: **zero blockers**. No footage or secrets were ever committed. Only the internal agent files remain to move out.

---

## The three honest takeaways for the end of the episode

1. **What works today:** the computer finds back attacks on its own (~0.75), the finish model gives sensible, explainable numbers, and the HP meter's timing matches published physiology.
2. **What doesn't yet:** the computer can't see the choke details by itself, the exact start of a choke is still hard, and with 73 attempts most effects are still uncertain.
3. **What fixes it:** labels, especially failed chokes. 64 of 73 attempts come from fights that ended in a finish, and failure rounds are what make the rates honest. Every labeling session improves the detector, the model and the science at once.
