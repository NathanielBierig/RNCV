# Pose coverage inside labeled attempts

rncv_pose_v1.onnx + RTMO-m fallback (CPU), score 0.25 / nms 0.65, two-fighter selection with the referee filter, stride 2. Gate (PLAN 2b): both fighters tracked in >= 60% of frames.

| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK | RNC-usable | RNC-usable (low bar) | Context |
|---|---|---|---|---|---|---|---|---|---|
| 1 | elkins_johnson_r2.mp4 | position_change | 2.3-9.4 | 108 | 🟢 96% | 78% | 14% | 54% | scramble |
| 2 | elkins_johnson_r2.mp4 | tap | 20.9-30.6 | 147 | 🟢 68% | 65% | 29% | 31% | ground_back |
| 3 | sterling_sandhagen.mp4 | position_change | 1.1-18.4 | 260 | 🟢 99% | 90% | 73% | 73% | standing_back |
| 4 | sterling_sandhagen.mp4 | escape | 38.6-48.4 | 147 | 🟢 100% | 100% | 31% | 74% | ground_back |
| 5 | sterling_sandhagen.mp4 | tap | 51.0-62.7 | 176 | 🟢 100% | 75% | 32% | 64% | turtle_ride |
| 6 | formiga_nguyen_r3_b.mp4 | unconscious | 15.8-24.4 | 104 | 🟢 84% | 65% | 50% | 70% | ground_back |
| 7 | pantoja_asakura_r2_b.mp4 | unconscious | 19.8-38.8 | 285 | 🟢 89% | 85% | 60% | 63% | ground_back |
| 8 | f21_blachowicz_pereira_r1.mp4 | position_change | 127.8-145.5 | 531 | 🟢 93% | 89% | 43% | 59% | turtle_ride |
| 9 | f21_blachowicz_pereira_r1.mp4 | escape | 221.1-229.5 | 253 | 🟢 100% | 87% | 33% | 53% | turtle_ride |
| 10 | f21_blachowicz_pereira_r1.mp4 | position_change | 247.7-259.9 | 366 | 🟢 95% | 92% | 45% | 57% | turtle_ride |
| 11 | f21_blachowicz_pereira_r1.mp4 | escape | 273.1-278.8 | 173 | 🟢 72% | 32% | 26% | 29% | turtle_ride |
| 12 | f21_blachowicz_pereira_r1.mp4 | bell | 301.6-302.0 | 13 | 🟢 100% | 100% | 54% | 77% | scramble |
| 13 | olivera_hoolowar_r1.mp4 | escape | 8.9-38.0 | 436 | 🟢 81% | 58% | 26% | 44% | ground_back |
| 14 | olivera_hoolowar_r1.mp4 | position_change | 43.8-72.5 | 430 | 🟢 67% | 61% | 18% | 27% | scramble |
| 15 | olivera_hoolowar_r1.mp4 | position_change | 76.1-109.6 | 504 | 🟢 85% | 75% | 20% | 59% | scramble |
| 16 | olivera_hoolowar_r1.mp4 | escape | 148.5-158.0 | 142 | 🟢 99% | 96% | 22% | 33% | ground_back |

Median both-tracked across 16 attempts: **94%**; 16/16 attempts pass the gate.
Median **RNC-usable (low bar)**: **58%** (defender head + a shoulder; choker's wrist/elbow at the neck or knee/ankle at the waist, choker joints accepted at confidence >= 0.1). By context: ground_back 54% (n=6); scramble 56% (n=4); standing_back 73% (n=1); turtle_ride 57% (n=5)
Median **RNC-usable** frames: **32%** (defender head + both shoulders, attacker head + one shoulder close to the defender's head; the attacker's arms may be hidden, see `rnc_ok` in src/pose_attempts.py).

Re-run after the Kaggle fine-tune with the new model to compare (same command).

## Visual check of the landmark samples (2026-10-21, 3 of 15 looked at by eye)
- **The coverage numbers overstate quality.** "Tracked" only means two skeletons exist, not that each sits on one real fighter.
- row05 (turtle, tap): the second skeleton is the **referee**; the real choker was missed (the referee filter let him through).
- row13 (Oliveira–Holloway, standing at the cage): one skeleton is **junk spread across the cage and background**.
- row07 (Pantoja–Asakura): the two skeletons **mix body parts** of both fighters (one fighter's head on the other's legs).
- Next: a small by-eye "correct pair" eval set, so the pose models are scored on correctness, not just existence.
