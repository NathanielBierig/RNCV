# Pose coverage inside labeled attempts

rncv_pose_v1.onnx (CPU), score 0.25 / nms 0.65, two-fighter selection with the referee filter, stride 2. Gate (PLAN 2b): both fighters tracked in >= 60% of frames.

| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK | RNC-usable |
|---|---|---|---|---|---|---|---|
| 1 | elkins_johnson_r2.mp4 | position_change | 2.3-9.4 | 108 | 🟢 86% | 81% | 17% |
| 2 | elkins_johnson_r2.mp4 | tap | 20.9-30.6 | 147 | 🟢 68% | 65% | 29% |
| 3 | sterling_sandhagen.mp4 | position_change | 1.1-18.4 | 260 | 🟢 92% | 87% | 70% |
| 4 | sterling_sandhagen.mp4 | escape | 38.6-48.4 | 147 | 🟢 100% | 100% | 31% |
| 5 | sterling_sandhagen.mp4 | tap | 51.0-62.7 | 176 | 🟢 94% | 85% | 34% |
| 6 | formiga_nguyen_r3_b.mp4 | unconscious | 15.8-24.4 | 104 | 🟢 67% | 61% | 39% |
| 7 | pantoja_asakura_r2_b.mp4 | unconscious | 19.8-38.8 | 285 | 🟢 83% | 80% | 65% |
| 8 | f21_blachowicz_pereira_r1.mp4 | position_change | 127.8-145.5 | 531 | 🔴 54% | 54% | 28% |
| 9 | f21_blachowicz_pereira_r1.mp4 | escape | 221.1-229.5 | 253 | 🟢 100% | 89% | 29% |
| 10 | f21_blachowicz_pereira_r1.mp4 | position_change | 247.7-259.9 | 366 | 🟢 84% | 78% | 36% |
| 11 | f21_blachowicz_pereira_r1.mp4 | escape | 273.1-278.8 | 173 | 🔴 17% | 17% | 8% |
| 12 | f21_blachowicz_pereira_r1.mp4 | bell | 301.6-302.0 | 13 | 🟢 100% | 100% | 54% |
| 13 | olivera_hoolowar_r1.mp4 | escape | 8.9-38.0 | 436 | 🔴 30% | 30% | 21% |
| 14 | olivera_hoolowar_r1.mp4 | position_change | 43.8-72.5 | 430 | 🔴 0% | 0% | 0% |
| 15 | olivera_hoolowar_r1.mp4 | position_change | 76.1-109.6 | 504 | 🔴 48% | 48% | 30% |
| 16 | olivera_hoolowar_r1.mp4 | escape | 148.5-158.0 | 142 | 🔴 38% | 38% | 18% |

Median both-tracked across 16 attempts: **76%**; 10/16 attempts pass the gate.
Median **RNC-usable** frames: **30%** (defender head + both shoulders, attacker head + one shoulder close to the defender's head; the attacker's arms may be hidden, see `rnc_ok` in src/pose_attempts.py).

Re-run after the Kaggle fine-tune with the new model to compare (same command).
