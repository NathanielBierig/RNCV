# Corner preview (red / blue)

`corner_preview.py` makes a preview video so you can see what the pose pipeline is doing:

- **Red and blue skeletons** = the two fighters it's tracking (thick = seen this frame, thin = filled in from the last pose, up to 0.5 s).
- **Label above each fighter:** corner, **pose score** (average joint confidence, 0–100%), seen/filled, and "upper body weak" when too few arm/shoulder joints are found.
- **"?" after RED/BLUE** = the corner is a guess. Corners are confirmed only when enough red or blue glove or trunk color is found near the wrists and hips. Modern UFC gloves are mostly black with small colored trim, so expect "?" often.
- **Thin gray skeletons** = people it dropped (crowd, referee, duplicate detections).
- **Top bar:** clip time, the running % of frames where both fighters are tracked, and the corner status.

```bash
C:/Users/netan/.venvs/rncv/Scripts/python -I tools/preview/corner_preview.py
```

Output: `data/pose/<clip>_corners.mp4` (local only). Known issue (see `research/pose_sweep/FINDINGS.md`): the referee is sometimes kept instead of a fighter. The preview shows this clearly when one skeleton stands apart from the pile.
