# Overlay renderer (Phase 6, built early)

Draws the submission type, the success probability (bar, colored red to green), an 8-second probability sparkline and the top 2 factors driving the prediction onto a recorded clip. It uses only the latest prediction at or before each frame, so it never peeks into the future.

- `overlay.py`: renders `--video` + `--preds` CSV → `--out` mp4. CSV columns: `t_s, sub_type, prob, factors` (factors are `;`-separated, prefixed `+`/`-`).
- `make_demo.py`: makes a synthetic clip + fake predictions for testing without real footage.

```bash
/c/Users/netan/.venvs/ufc-cv/Scripts/python make_demo.py
/c/Users/netan/.venvs/ufc-cv/Scripts/python overlay.py --video demo_clip.mp4 --preds demo_preds.csv --out demo_overlay.mp4
```

**Windows note:** OpenCV fails to load from a venv inside this project folder ("filename too long"), so the venv lives at the short path `C:\Users\netan\.venvs\ufc-cv`.

Later, Phase 5's model writes `preds.csv` and this renderer stays unchanged.
