# Pose coverage inside labeled attempts

RTMO-m (CPU), score 0.3 / nms 0.65, two-fighter selection with the referee filter, stride 2. Gate (PLAN 2b): both fighters tracked in >= 60% of frames.

| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK |
|---|---|---|---|---|---|---|
| 1 | elkins_johnson_r2.mp4 | position_change | 2.3-9.4 | 108 | 🟢 72% | 51% |
| 2 | elkins_johnson_r2.mp4 | tap | 20.9-30.6 | 147 | 🔴 33% | 22% |
| 3 | sterling_sandhagen.mp4 | position_change | 1.1-18.4 | 260 | 🟢 64% | 48% |
| 4 | sterling_sandhagen.mp4 | escape | 38.6-48.4 | 147 | 🟢 65% | 65% |
| 5 | sterling_sandhagen.mp4 | tap | 51.0-62.7 | 176 | 🟢 83% | 36% |
| 6 | formiga_nguyen_r3_b.mp4 | unconscious | 15.8-24.4 | 104 | 🔴 45% | 27% |
| 7 | pantoja_asakura_r2_b.mp4 | unconscious | 19.8-38.8 | 285 | 🔴 46% | 42% |
| 8 | f21_blachowicz_pereira_r1.mp4 | position_change | 127.8-145.5 | 531 | 🟢 72% | 69% |
| 9 | f21_blachowicz_pereira_r1.mp4 | escape | 221.1-229.5 | 253 | 🟢 96% | 71% |
| 10 | f21_blachowicz_pereira_r1.mp4 | position_change | 247.7-259.9 | 366 | 🟢 80% | 75% |
| 11 | f21_blachowicz_pereira_r1.mp4 | escape | 273.1-278.8 | 173 | 🟢 61% | 31% |
| 12 | f21_blachowicz_pereira_r1.mp4 | bell | 301.6-302.0 | 13 | 🔴 0% | 0% |

Median both-tracked across 12 attempts: **64%**; 8/12 attempts pass the gate.

Re-run after the Kaggle fine-tune with the new model to compare (same command).
