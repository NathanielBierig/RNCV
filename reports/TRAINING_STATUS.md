# Training status (Phase 2, VICOS)

**State: INTERRUPTED / not finished.** The first gradient-boosting run (`--model gbm`, 5 time-block folds) was still running when the laptop closed. No metrics yet.

Everything else is done: data loader, features, leak-free time-block folds, Kaggle notebook (identity matching tested 3270/3270), DOWNLOADS.md.

## Resume (from C:\Users\netan\projects\RNCV, PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data/raw/vicos
curl.exe -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
.venv\Scripts\python -I src/train_baseline.py --model gbm
.venv\Scripts\python -I src/train_baseline.py --model mlp
```

Outputs go to `reports/` (metrics_*.json, per_class_*.csv, confusion_*.png). The 209 MB annotations download took ~15 min last time; one gbm run is expected to take ~10–30 min on CPU (estimate).
