# Pose coverage inside labeled attempts

RTMO-m (CPU), score 0.3 / nms 0.65, two-fighter selection with the referee filter, stride 2. Gate (PLAN 2b): both fighters tracked in >= 60% of frames.

| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK |
|---|---|---|---|---|---|---|
| 1 | elkins_johnson_r2.mp4 | tap | 3.4-30.9 | 414 | 🟢 63% | 55% |
| 2 | elkins_johnson_r2.mp4 | position_change | 2.3-9.4 | 108 | 🟢 72% | 51% |
| 3 | elkins_johnson_r2.mp4 | tap | 20.9-30.6 | 147 | 🔴 33% | 22% |
| 4 | sterling_sandhagen.mp4 | position_change | 1.1-18.4 | 260 | 🟢 64% | 48% |
| 5 | sterling_sandhagen.mp4 | escape | 38.6-48.4 | 147 | 🟢 65% | 65% |
| 6 | sterling_sandhagen.mp4 | tap | 51.0-62.7 | 176 | 🟢 83% | 36% |
| 7 | formiga_nguyen_r3_b.mp4 | unconscious | 15.8-24.4 | 104 | 🔴 45% | 27% |

Median both-tracked across 7 attempts: **64%**; 5/7 attempts pass the gate.

Re-run after the Kaggle fine-tune with the new model to compare (same command).
