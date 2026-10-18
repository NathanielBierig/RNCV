# Your tasks (most urgent first)

Owned by the secretary session, which keeps this list current. Tick a box when done and tell the secretary. Times are estimates.

## 🔴 Now (unblocks everything else)

- [ ] **1. Ask a training partner to be the second rater** (5 min): someone who knows BJJ and can code about 30 attempts later (about 1–2 h of their time). Ask now, since it has the longest lead time. Message to send:
  > "I'm doing a data project on UFC rear-naked chokes. Could you label ~30 short clips for me (hooks vs body triangle, arm under chin, etc.)? About an hour, I'll show you the tool."
- [ ] **2. Read and approve the pre-registration** (10 min): [research/rnc_science/PREREG.md](research/rnc_science/PREREG.md). Reply "approve PREREG" or say what to change. It gets frozen (committed with a timestamp) before any labeling, which makes the science credible.
- [ ] **3. Save 3 UFC RNC clips locally for the pose smoke test** (20 min). This is Phase 2b, the biggest technical risk: does pose survive tangled cage footage?
  - Watch through [UFC Fight Pass](https://ufcfightpass.com/) or [UFC on YouTube](https://www.youtube.com/@ufc). Save **only the attempt**: about 30 s before the finish to the tap. One way is screen recording with [OBS](https://obsproject.com/) (free).
  - Put the clips in `C:\Users\netan\projects\RNCV\data\clips\` (git ignores this folder). Never upload them anywhere (see [docs/FOOTAGE.md](docs/FOOTAGE.md)).
  - Suggested fights (recent HD RNC finishes; finish time in the round in brackets):

    | Fight | Round (time) | Stats page |
    |---|---|---|
    | Brendan Allen vs Christian Leroy Duncan, 2026-10-10 | R5 (2:46) | [ufcstats](http://ufcstats.com/fight-details/7db1a3dac7e343e7) |
    | Brady Hiestand vs Rinya Nakamura, 2026-09-26 | R2 (4:07) | [ufcstats](http://ufcstats.com/fight-details/29423f522e76f12e) |
    | Rei Tsuruya vs Kevin Borjas, 2026-08-29 | R1 (4:14) | [ufcstats](http://ufcstats.com/fight-details/ec5281a72f09d8ac) |

  - Name them `allen_duncan_r5.mp4`, `hiestand_nakamura_r2.mp4`, `tsuruya_borjas_r1.mp4`.

## 🟡 Soon (this week)

- [ ] **4. Kaggle account + phone verification** (10 min). Phone verification is needed for free GPU. [Sign up](https://www.kaggle.com/account/login?phase=startRegisterTab), then verify your phone at [kaggle.com/settings](https://www.kaggle.com/settings).
- [ ] **5. Pilot: label 15 RNC attempts** (about 1–1.5 h) with the labeling tool (`tools/labeler/`, being built). The secretary will send the exact fight list with direct links and timestamps. Keep a stopwatch running: it measures the real cost per attempt.
- [ ] **6. Phase 5 and 6 decision** (15 min read): a review memo with options is being written (`docs/DECISION_PHASE5_6.md`). You pick before we commit heavily.

## ⚪ Later

- [ ] 7. Label about 150 attempts total (about 8–12 h at about 4 min each with the pre-labeler; estimate, measured in the pilot).
- [ ] 8. Second rater codes about 30 attempts.
