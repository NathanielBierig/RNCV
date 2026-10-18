"""Make a synthetic test clip + fake predictions so overlay.py can be tested without real footage."""
import cv2
import numpy as np
import pandas as pd

FPS, W, H, SECS = 30, 960, 540, 12

writer = cv2.VideoWriter("demo_clip.mp4", cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
for n in range(FPS * SECS):
    frame = np.full((H, W, 3), (40, 70, 40), np.uint8)
    cx = W // 2 + int(80 * np.sin(n / 20))
    cv2.circle(frame, (cx, H // 2), 60, (200, 200, 200), -1)  # stand-in "fighters"
    cv2.circle(frame, (cx + 70, H // 2 + 20), 55, (150, 150, 220), -1)
    writer.write(frame)
writer.release()

# No attempt for 2 s, then an RNC whose probability rises, dips (hand fight), then climbs to a finish.
rows = []
for t in np.arange(0, SECS, 0.5):
    if t < 2:
        rows.append((t, "", 0.0, ""))
        continue
    p = float(np.clip(0.2 + 0.08 * (t - 2) - (0.25 if 5 <= t < 7 else 0), 0.02, 0.97))
    f = "-2-on-1 hand fight;+body triangle" if 5 <= t < 7 else "+body triangle;+arm under chin"
    rows.append((t, "RNC", p, f))
pd.DataFrame(rows, columns=["t_s", "sub_type", "prob", "factors"]).to_csv("demo_preds.csv", index=False)
print("wrote demo_clip.mp4, demo_preds.csv")
