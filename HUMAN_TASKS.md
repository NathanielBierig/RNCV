# Your tasks (most urgent first)

Owned by the secretary session, which keeps this list current. Tick a box when done and tell the secretary. Times are estimates.

## 🔴 Now (unblocks everything else)

- [ ] **1. Ask a training partner to be the second rater** (5 min): someone who knows BJJ and can code about 30 attempts later (about 1–2 h of their time). Ask now, since it has the longest lead time. Message to send:
  > "I'm doing a data project on UFC rear-naked chokes. Could you label ~30 short clips for me (hooks vs body triangle, arm under chin, etc.)? About an hour, I'll show you the tool."
- [ ] **2. Read and approve the pre-registration** (10 min): [research/rnc_science/PREREG.md](research/rnc_science/PREREG.md). Reply "approve PREREG" or say what to change. It gets frozen (committed with a timestamp) before any labeling, which makes the science credible.
- [ ] **3. Save 3 UFC RNC clips locally for the pose smoke test** (20 min). This is Phase 2b, the biggest technical risk: does pose survive tangled cage footage?
  - Watch through [UFC Fight Pass](https://ufcfightpass.com/) or [UFC on YouTube](https://www.youtube.com/@ufc). Save **only the attempt**: about 30 s before the finish to the tap. One way is screen recording with [OBS](https://obsproject.com/) (free).
  - Put the clips in `C:\Users\netan\projects\RNCV\data\clips\` (git ignores this folder). Never upload them anywhere (see [docs/FOOTAGE.md](docs/FOOTAGE.md)).
  - Suggested fights: all **main events**, so they are easy to find on Paramount+ (finish time is the time in the round; record from ~30 s before it to the tap):

    | Fight | Event | Round (time) | Stats page |
    |---|---|---|---|
    | Dricus Du Plessis vs Israel Adesanya | UFC 305, 2024-08-17 | R4 (3:38) | [ufcstats](http://ufcstats.com/fight-details/6c44af21414e4143) |
    | Charles Oliveira vs Mateusz Gamrot | UFC Fight Night, 2025-10-11 | R2 (2:48) | [ufcstats](http://ufcstats.com/fight-details/79865287be90e4be) |
    | Brendan Allen vs Christian Leroy Duncan | UFC Fight Night, 2026-10-10 | R5 (2:46) | [ufcstats](http://ufcstats.com/fight-details/7db1a3dac7e343e7) |

    Backups (also main events): Pantoja vs Asakura (UFC 310, R2 2:05), Bautista vs Oliveira (2026-02-07, R2 4:46). Skipped on purpose: Silva vs Delgado (one-armed choke, atypical).

  - Name them `duplessis_adesanya_r4.mp4`, `oliveira_gamrot_r2.mp4`, `allen_duncan_r5.mp4`.

## 🟡 Soon (this week)

- [ ] **4. Kaggle account + phone verification** (10 min). Phone verification is needed for free GPU. [Sign up](https://www.kaggle.com/account/login?phase=startRegisterTab), then verify your phone at [kaggle.com/settings](https://www.kaggle.com/settings).
- [ ] **5. Pilot: label 15 RNC attempts** (about 1–1.5 h) with the labeling tool (`tools/labeler/` is built; waits for task 2). Fight draw: [phase3_labels/PILOT.md](phase3_labels/PILOT.md). The secretary will send the exact fight list with direct links and timestamps. Keep a stopwatch running: it measures the real cost per attempt.
- [ ] **6. Phase 5 and 6 decision** (15 min read): read [docs/DECISION_PHASE5_6.md](docs/DECISION_PHASE5_6.md). My recommendation there: 5-B (factor model + live hazard model) and 6-A (offline renderer on recorded clips). Reply with your pick.

## ⚪ Later

- [ ] 7. Label about 150 attempts total (about 8–12 h at about 4 min each with the pre-labeler; estimate, measured in the pilot).
- [ ] 8. Second rater codes about 30 attempts.
