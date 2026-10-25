# Overlay renderer (Phase 6, built early)

Draws the submission type, the success probability (bar, colored red to green), an 8-second probability sparkline and the top 2 factors driving the prediction onto a recorded clip. It uses only the latest prediction at or before each frame, so it never peeks into the future.

- `overlay.py`: renders `--video` + `--preds` CSV → `--out` mp4. CSV columns: `t_s, sub_type, prob, factors` (factors are `;`-separated, prefixed `+`/`-`).
- `make_demo.py`: makes a synthetic clip + fake predictions for testing without real footage.

```bash
python make_demo.py
python overlay.py --video demo_clip.mp4 --preds demo_preds.csv --out demo_overlay.mp4
```

**Windows note:** if OpenCV fails to load ("filename too long"), create the venv at a short path (e.g. `C:envsncv`).

Later, Phase 5's model writes `preds.csv` and this renderer stays unchanged.
