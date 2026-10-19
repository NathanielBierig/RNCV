# Your tasks (most urgent first)

Owned by the secretary session. Tick a box when done and tell the secretary. Times are estimates. Nothing here is urgent tonight; it is queued for when you have time.

## 🟢 Done
- [x] PREREG frozen (commit b8d817d)
- [x] `gh` installed and signed in
- [x] 3 clips saved in `data\clips\` (Pantoja–Asakura, Sterling–Sandhagen, GSP–Bisping)
- [x] Red/blue corner previews watched, they looked good

## 🔴 Open tasks, in order

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
