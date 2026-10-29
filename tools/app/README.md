# Test the detector (local app)

Drop a UFC clip, and the real attempt detector analyses it. Then play it back with the readouts: detector status, finish chance, defender HP with an estimate of the seconds of air left, and the factor boxes. Everything runs on your laptop. Clips go to `data/app_uploads/` (git-ignored) and nothing is uploaded anywhere.

```bash
python -I tools/app/serve.py
```
Then open http://localhost:8765. It uses the image-features environment (open_clip, torch, onnxruntime, scikit-learn, OpenCV), the fine-tuned pose model in `models/` for the fighter crop, and the cached detector features in `data/attempt_clf/`.

- **Detector:** detector v2 (`research/attempt_clf/detector_v2.py`), trained once at startup on every labeled fight. It analyses **2 minutes** from where you are in the video (clips of 2 minutes or less are analysed whole), so a long video never costs more than that. Hysteresis: on above 0.55, off after 2 s below 0.30.
- **Test pool** (`data/clips/test_pool/`): 1–2 minute clips of fights **never used for training**, e.g. pre-2018 fights outside the study window (Diaz vs McGregor 1, UFC 196). They show up as one-click demos.
  - **Diaz vs McGregor 1** (full broadcast, 2-min cut): detector peak 0.78 as Diaz takes the back, 13 s before the tap.
  - **Demian Maia top finishes** (UFC highlight reel, first 2 min, pre-2018): the detector **never fires** (mean score 0.25, nothing above 0.55) despite several back-take chokes. A highlight reel's fast cuts and close-ups don't look like the full-round broadcasts it was trained on. This is an honest limit: it doesn't carry over to edited highlights yet.
- **Your keys drive the finish model:** `1` arm, `2` grip, `3` legs, `4` 2-on-1, `5` hand hidden, `6` flattened, `7` chin tucked (each cycles through its values, then "unknown"), `S`/`E` attempt start/end, `R` reset. The finish model and HP are model v0.8, exported by `export_model.py` to `model.json`. `node tools/app/check_model.js` checks the browser port against Python.
- **Honest limits:** the computer can't see the factors yet (reports/factor_pilot.md), so they come from you. The detector finds back attacks (frame ROC-AUC ~0.75) but not the exact second the choke starts.
