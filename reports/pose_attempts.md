# Pose coverage inside labeled attempts

RTMO-m (CPU), score 0.3 / nms 0.65, two-fighter selection with the referee filter, stride 2. Gate (PLAN 2b): both fighters tracked in >= 60% of frames.

| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK | RNC-usable |
|---|---|---|---|---|---|---|---|
| 1 | elkins_johnson_r2.mp4 | position_change | 2.3-9.4 | 108 | 🟢 72% | 51% | 18% |
| 2 | elkins_johnson_r2.mp4 | tap | 20.9-30.6 | 147 | 🔴 33% | 22% | 8% |
| 3 | sterling_sandhagen.mp4 | position_change | 1.1-18.4 | 260 | 🟢 64% | 48% | 27% |
| 4 | sterling_sandhagen.mp4 | escape | 38.6-48.4 | 147 | 🟢 65% | 65% | 27% |
| 5 | sterling_sandhagen.mp4 | tap | 51.0-62.7 | 176 | 🟢 83% | 36% | 23% |
| 6 | formiga_nguyen_r3_b.mp4 | unconscious | 15.8-24.4 | 104 | 🔴 45% | 27% | 3% |
| 7 | pantoja_asakura_r2_b.mp4 | unconscious | 19.8-38.8 | 285 | 🔴 46% | 42% | 22% |
| 8 | f21_blachowicz_pereira_r1.mp4 | position_change | 127.8-145.5 | 531 | 🟢 72% | 69% | 29% |
| 9 | f21_blachowicz_pereira_r1.mp4 | escape | 221.1-229.5 | 253 | 🟢 96% | 71% | 30% |
| 10 | f21_blachowicz_pereira_r1.mp4 | position_change | 247.7-259.9 | 366 | 🟢 80% | 75% | 26% |
| 11 | f21_blachowicz_pereira_r1.mp4 | escape | 273.1-278.8 | 173 | 🟢 61% | 31% | 20% |
| 12 | f21_blachowicz_pereira_r1.mp4 | bell | 301.6-302.0 | 13 | 🔴 0% | 0% | 0% |
| 13 | olivera_hoolowar_r1.mp4 | escape | 8.9-38.0 | 436 | 🟢 63% | 41% | 10% |
| 14 | olivera_hoolowar_r1.mp4 | position_change | 43.8-72.5 | 430 | 🟢 78% | 72% | 21% |
| 15 | olivera_hoolowar_r1.mp4 | position_change | 76.1-109.6 | 504 | 🟢 90% | 63% | 12% |
| 16 | olivera_hoolowar_r1.mp4 | escape | 148.5-158.0 | 142 | 🟢 96% | 87% | 19% |

Median both-tracked across 16 attempts: **68%**; 12/16 attempts pass the gate.
Median **RNC-usable** frames: **20%** (defender head + both shoulders, attacker head + one shoulder close to the defender's head; the attacker's arms may be hidden, see `rnc_ok` in src/pose_attempts.py).

Re-run after the Kaggle fine-tune with the new model to compare (same command).
