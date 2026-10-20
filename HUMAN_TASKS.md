# Your tasks (most urgent first)


# ☀️ Tomorrow (do in this order, one action per line)

Work day tomorrow, so this is the short version. Estimates: Kaggle setup 15 min, clips 30 min, labeling 20 min per sitting.

## Step 0: Tag women's fights out of scope (1 min)
1. Open the **Main** session in the Claude app (the one called "UFC submission detection CV system") and send: `tag women's fights out of scope in the queues`. (PREREG amendment A1, men's only, is already committed. Main does the tagging in the queue files.)
2. Then tell the **Secretary** session (this one): "refresh the Google Sheets from the queues". It re-uploads the successes sheet and adds a failures sheet to your Drive folder RNCV, with women's fights marked.
3. Excel is not needed. You use Google Sheets.

## Step 1 ✅ DONE: Kaggle fine-tune finished (COMPLETE) and Main downloaded it by CLI. Old clicks below kept for reference. It runs about 4-6 h by itself (15 min of clicks)
Do this first so it trains while you work. Full guide: [docs/KAGGLE_FINETUNE.md](docs/KAGGLE_FINETUNE.md). No UFC video goes to Kaggle.
1. Go to kaggle.com and sign in (sign up first if you have no account).
2. Click your **profile picture** (top right) > **Settings** > **Phone verification** > enter your phone and the code.
3. Click **Create** (left menu) > **New Notebook**.
4. Click **File** > **Import Notebook** > **Browse files**. Choose `C:\Users\netan\projects\RNCV\notebooks\kaggle_finetune_pose\finetune.ipynb`. Click **Import**.
5. Open the right sidebar (the **<** arrow, top right) > **Session options**.
6. **Accelerator** > **GPU T4 x1** > confirm.
7. **Internet** > **On**.
8. Click **Save Version** (top right) > choose **Save & Run All (Commit)** > **Save**. This keeps running with the browser closed, for up to 12 h. Do not pick plain "Run All" (it stops if the tab closes).
9. Close the tab.

**What success looks like:** later, kaggle.com > **Your Work** > the notebook > **Versions** shows "Successful", and the **Output** tab lists `rncv_pose_v1.onnx` (about 80 MB) plus `rncv_pose_v1_results.md`.
**If it errors:** open the version > **Logs**, scroll to the first red error, take a screenshot and paste it to the Main session. Re-running is safe.

## Step 2: Download 10 clips (30 min)
Rule: skip women's fights. Take **3 clips, then label them (Step 3)**, then the next 3. Do not download all 10 first.

For each row below: search YouTube for `[fighter 1] vs [fighter 2] full fight` on the official **@UFC** channel. Open the video, scrub to the round, and find the choke (it starts about 60 s before the finish; the clock time to jump to is in the table). Write down two video times: where it starts, and a few seconds after it ends. Then paste this in a **new PowerShell** window, filling in the three CAPS parts:
```powershell
cd C:\Users\netan\projects\RNCV
yt-dlp --download-sections "*START-END" --force-keyframes-at-cuts -f "bv*+ba/b" --merge-output-format mp4 -o "data/clips/NAME.%(ext)s" "LINK"
```
Example for START-END: `14:39-14:52`. If you cannot find the fight in 10 minutes, write `unwatchable` in the sheet and take the next row. Or send me the link and times and I make the command for you.

| # | Queue | Fight | Round | Jump to round clock | NAME to use |
|---|---|---|---|---|---|
| 1 | success 311 | Jussier Formiga vs Ben Nguyen | R3 | 4:17 | already saved: `formiga_nguyen_r3` (label this first) |
| 2 | success 310 | Robert Sanchez vs Joby Sanchez | R1 | 4:10 | `s310_sanchez_sanchez_r1` |
| 3 | success 309 | Geoff Neal vs Brian Camozzi | R1 | 3:12 | `s309_neal_camozzi_r1` |
| 4 | success 308 | Charles Byrd vs John Phillips | R1 | 2:02 | `s308_byrd_phillips_r1` |
| 5 | success 307 | Dmitry Sosnovskiy vs Mark Godbeer | R2 | 1:31 | `s307_sosnovskiy_godbeer_r2` |
| 6 | success 306 | Antonio Carlos Junior vs Tim Boetsch | R1 | 1:32 | `s306_acj_boetsch_r1` |
| 7 | success 305 | Markus Perez vs James Bochnovic | R1 | 1:32 | `s305_perez_bochnovic_r1` |
| 8 | failure 2 | Kevin Holland vs Randy Brown (2026-04-11) | R2 | watch the whole round | `f2_holland_brown_r2` |
| 9 | failure 3 | Asu Almabayev vs Jose Ochoa (2025-07-26) | R1 | watch the whole round | `f3_almabayev_ochoa_r1` |
| 10 | failure 4 | Jeremiah Wells vs Themba Gorimbo (2025-11-01) | R3 | watch the whole round | `f4_wells_gorimbo_r3` |

Skipped as women's fights: success 313, 312, 303, 302, 297. More men's rows if you need them: success 304, 301, 300, 299. For failure rows there is no known finish, so clip the part of the round where an RNC is tried. If there is none, the label is "no RNC in this round", which is a valid result. Also: the success rows above are all recent-to-old from the bottom of the sheet; recent fights (2025-26) are more likely Paramount+ only.

## Step 3: Labeling loop (about 20 min per sitting, 3 clips)
Current guide: [docs/LABELING_GUIDE.md](docs/LABELING_GUIDE.md) (workflow, how to judge each field, G / X keys, clock, Link). Picture code book: [docs/rnc_codebook.html](docs/rnc_codebook.html). The old Google Doc is superseded.
1. Open `tools\labeler\index.html` in Chrome. Press **F5**.
2. Click **Load fight list(s) CSV** and select the three queue files (hold Ctrl): `labeling_queue_successes.csv`, `labeling_queue_failures.csv`, `random_10.csv`.
3. Click **Link labels.csv** and choose `phase3_labels\labels.csv` (**not** a queue file; the tool now refuses those).
4. Pick the fight, click **Open video**, choose the clip.
5. Press **C** (type the clock), **S** (start), fill the panel, **Space**, **E** (end), fill the outcome, Enter.
6. If the ref or camera blocks the view, press **X** in the panel.
6b. **Press G** whenever something changes after the 2-second freeze (body lock added, hooks in or out, arm moves, and so on). Pick only the field that changed, then Enter. Reload with F5 first.
7. Type `pilot` in the notes for the first 15 labels.
8. Repeat for clips 2 and 3, then go back to Step 2 for the next 3.

## Step 4 ✅ DONE by Main (modelsncv_pose_v1.onnx is in place). Old steps kept for reference:
1. Kaggle > **Your Work** > the notebook > **Versions** > the finished version > **Output** tab.
2. Download `rncv_pose_v1.onnx`, `rncv_pose_v1_results.md`, `rncv_pose_v1_metrics.json` and `yolo_pose_onnx.py`.
3. Move `rncv_pose_v1.onnx` into `C:\Users\netan\projects\RNCV\models\` (create `models` if it does not exist).
4. Tell the Main session: **swap in the fine-tuned pose model**.

---
# Everything else (older list)

Owned by the secretary session. Tick a box when done and tell the secretary. Times are estimates. Nothing here is urgent tonight; it is queued for when you have time.

## 🟢 Done
- [x] PREREG frozen (commit b8d817d)
- [x] `gh` installed and signed in
- [x] 3 clips saved in `data\clips\` (Pantoja–Asakura, Sterling–Sandhagen, GSP–Bisping)
- [x] Red/blue corner previews watched, they looked good

## 🔴 Open tasks, in order

- [ ] **0a. Two quick answers for Main** (2 min): (1) keep Elkins row 1 (113.4-140.9) or rows 2+3? (2) OK to add `compilation` to the 3 Sterling rows and `pilot` to the first 15 rows at commit time? Close the labeler tab first, then Main edits `labels.csv`. Check: [reports/labels_qa.md](reports/labels_qa.md).
- [ ] **0. Approve PREREG amendment A2** (new `upper_body` variable: body_lock / seatbelt / none). Main is asking you. Recommended: approve, it is descriptive only.

- [ ] **1. Pilot labeling, in short sittings** (3–5 attempts per sitting, 15–20 min). Open `tools/labeler/index.html` in Chrome or Edge, click "Link labels.csv" so every save is written, and follow [phase3_labels/PILOT.md](phase3_labels/PILOT.md) (8 successes + 7 failures). Timing is logged automatically. **Step-by-step: see "How to label" at the bottom of this file.**
- [ ] **2. Read [docs/CODE_TOUR.md](docs/CODE_TOUR.md)** (30 min).
- [ ] **3. Decide corner (red/blue) labeling:** (a) one click per clip in the UI ("this skeleton is red"), or (b) pull red/blue from fight data (ufcstats/Tapology) and match by appearance. The main session will recommend one.
- [ ] **4. Housekeeping:** archive idle helper sessions in the RNCV sidebar group (chief-of-staff, critic, entrepreneur, ufc-labels, code-tour, build-phase2). Keep Main and Secretary.
- [ ] **5. Second rater:** ask a training partner, if not done yet (5 min). Suggested message: "I'm doing a data project on UFC rear-naked chokes. Could you label ~30 short clips for me (hooks vs body triangle, arm under chin, etc.)? About an hour, I'll show you the tool."
- [ ] **6. Decide whether helper sessions may commit** (CLAUDE.md currently says main session only).

## 🟡 Soon
- [ ] Kaggle account + phone verification (10 min): [sign up](https://www.kaggle.com/account/login?phase=startRegisterTab), then [kaggle.com/settings](https://www.kaggle.com/settings).
- [ ] Read [docs/DECISION_PHASE5_6.md](docs/DECISION_PHASE5_6.md) and pick (recommended: 5-B + 6-A).

## ⚪ Later
- [ ] Label about 150 attempts total (about 8–12 h, an estimate measured in the pilot).
- [ ] Second rater codes about 30 attempts.

---

# How to label (repeat these steps each sitting)

You label **one clip at a time**. A sitting = 3–5 clips (15–20 min). Do the same steps every time.

## A. Get one clip (about 3 min)
1. Open [phase3_labels/labeling_queue_successes.csv](phase3_labels/labeling_queue_successes.csv) (Excel is fine). Take the next row without `status` filled in. Columns you need: `attacker`, `defender`, `round`, `known_finish_elapsed` (the finish time in the round), `ufc_youtube_channel_search` (a link: click it).
2. Find the fight on the official UFC YouTube channel (or the free-fight video on Paramount+/Fight Pass). If you can't find it legally in **10 minutes**, write `unwatchable` in the `status` column and take the next row. Never skip a row because it looks hard.
3. In the video, find the **round** and note two times (video timestamps, like 41:25): where the choke attempt starts (or about 60 s before the finish if unsure) and a few seconds after the end.
4. Send me: the YouTube link and the two timestamps, e.g. `https://youtu.be/XXXX 41:15 to 41:50, Allen vs Duncan R5`. I send you back one command.
5. Paste that command into PowerShell (open it in the RNCV folder). The clip appears in `data\clips\`. It stays on your laptop only, never uploaded.

(The command I send looks like this; you only change nothing):
```powershell
yt-dlp --download-sections "*41:15-41:50" --force-keyframes-at-cuts -f "bv*+ba/b" --merge-output-format mp4 -o "data/clips/allen_duncan_r5.%(ext)s" "https://www.youtube.com/watch?v=XXXX"
```

## B. Open the labeler (once per sitting, 1 min)
1. Double-click `tools\labeler\index.html`. Use **Chrome or Edge**.
2. Click **Load fight list(s) CSV** and select `labeling_queue_successes.csv`, `labeling_queue_failures.csv` and `random_10.csv` (hold Ctrl to pick all three).
3. Click **Link labels.csv**, choose `phase3_labels\labels.csv` (it's created if missing). Now every save is written to the file.
4. Pick your fight in the **Fight** dropdown. If the *other* fighter is the one choking, press **W**.
5. Click **Open video** and pick your clip from `data\clips\`.

## C. Label the attempt (about 4 min)
1. **C**: pause on a frame where the round clock is visible, type the time **remaining** (like `3:12`), Enter. This syncs the clock.
2. Scrub to where the choke starts: back control, arm across the neck, second hand locking. Press **S** (start).
3. The video **plays 2 seconds and freezes**. You haven't seen the ending, on purpose. A panel opens: for each field press the number key that matches what you see, then **Enter**. Leave a field blank if you can't see it. Don't guess.
4. Press **Space** to play on. If the grip changes, press **T** then a number.
5. At the tap, stoppage, escape or bell, press **Space** to pause then **E** (end).
6. Outcome panel: pick the outcome (number key), Enter. If you made a mistake, press **U** to undo the last row.
7. Look at the stopwatch note: timing is logged automatically. You don't need to time yourself.

## D. Edge cases
- **View blocked (ref or camera in the way):** in the factor panel press **X**. Every field is left blank, the panel closes and the attempt is flagged `view_blocked`. Press X during the attempt to toggle the flag. Reload `index.html` (F5) first; saved rows are kept.
- **Picture cheat sheet for the 12 questions:** https://claude.ai/artifact/6nubSqJW1YPKfeZy13ECBE
- Atypical choke (one-armed, chin-linked): code it as normal and choose the **one_arm** style. It is excluded from the main model later, but you still label it.
- Two fighters named wrong way round: press **W**.
- Clock sync warning (end is more than 3 s from the stats time): redo step C1.
- Unsure about a field: leave blank. "Unclear" is a valid answer.

## E. Where do more clips come from?
Same method, from the queues in `phase3_labels/`: `labeling_queue_successes.csv` (finishes, most recent first), `labeling_queue_failures.csv` (rounds with failed attempts), and `random_10.csv` (10 random full fights, a separate job). Pilot session 1 = successes ranks 1–8 and failures ranks 1–7.
- Recent (2025–26) fights may be Paramount+ only, not on YouTube. If so, record from Paramount+ instead, or mark `unwatchable` and move on.
- The three test clips (Pantoja, Sterling, GSP) are for the pose test, not labeling, unless they're in the queue.
- Silva vs Delgado is in session 1 and was one-armed: label it, tag it `one_arm`.
