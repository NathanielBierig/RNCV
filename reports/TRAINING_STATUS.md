# Training status (Phase 2, VICOS)

**State: first baseline FINISHED** (`--model gbm`, 5 time-block folds, ~23 min on CPU). The MLP comparison has not been run yet.

| Metric (pooled out-of-fold) | Value |
|---|---|
| Macro-F1 | **0.46** (per fold 0.45–0.66) |
| Balanced accuracy | **0.47** |
| Accuracy | 0.55 |
| Always-guess-majority-class baseline | 0.14 |

**Works:** standing 0.92 F1, turtle 0.73–0.81, open guard 0.75–0.77, closed_guard1 0.66, back 0.59–0.65, 50-50 0.57.
**Fails:** half_guard1/2 (0.05/0.08), side_control2 0.14, closed_guard2 0.14, mount2 0.21, side_control1 0.23, takedown2 0.24.
**Hypothesis:** the failures are the "which athlete is on top" pairs. Both halves score far below a 50/50 guess, so the model probably finds the position but swaps the roles. Next check: save out-of-fold predictions and score on 10 positions (roles merged), then add role-invariant features (e.g. "top athlete" = whoever's hips are higher in the image) or a two-stage model (position, then role).

Caveat: train and test share athletes and session, so this is an optimistic upper bound for UFC footage.

## Re-run / continue (from C:\Users\netan\projects\RNCV, PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data/raw/vicos
curl.exe -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
.venv\Scripts\python -I src/train_baseline.py --model gbm
.venv\Scripts\python -I src/train_baseline.py --model mlp
```
