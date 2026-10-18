"""Phase 2 baseline: 18-class BJJ position classifier on VICOS keypoints (CPU).

Splits are group-aware: each fold holds out one contiguous time block of every
sparring sequence, across all cameras, with a purge buffer around it (see
vicos_data.time_block_folds). Random frame-level splits are never used, because
neighbouring frames and other camera views of the same moment would leak.

Usage:
    python -I src/train_baseline.py --model gbm       # gradient boosting (default)
    python -I src/train_baseline.py --model mlp       # small MLP for comparison
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)

import features
import vicos_data

ROOT = Path(__file__).resolve().parents[1]


def make_model(kind, n_classes):
    if kind == "gbm":
        # sklearn's LightGBM-style booster: handles NaN natively, no extra DLL
        # (LightGBM's DLL fails to load under this app's long sandboxed path).
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.08, max_leaf_nodes=31,
            min_samples_leaf=40, l2_regularization=1.0, max_features=0.7,
            class_weight="balanced", early_stopping=False, random_state=0)
    from sklearn.impute import SimpleImputer
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0.0, add_indicator=False),
        StandardScaler(),
        MLPClassifier(hidden_layer_sizes=(256, 128), alpha=1e-3, batch_size=512,
                      learning_rate_init=1e-3, max_iter=40, early_stopping=True,
                      random_state=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["gbm", "mlp"], default="gbm")
    ap.add_argument("--blocks", type=int, default=5, help="time blocks per sequence = folds")
    ap.add_argument("--purge", type=int, default=300, help="frames dropped around each test block")
    ap.add_argument("--train-stride", type=int, default=2,
                    help="use every k-th training frame (neighbours are near-duplicates)")
    ap.add_argument("--annotations", default=str(vicos_data.DEFAULT_PATH),
                    help="VICOS-format JSON (original, or re-extracted by the Kaggle notebook)")
    ap.add_argument("--tag", default="", help="suffix for report filenames")
    args = ap.parse_args()

    meta, poses = vicos_data.load(args.annotations)
    X, names = features.build(poses)
    classes = sorted(meta["position"].unique())
    y = meta["position"].map({c: i for i, c in enumerate(classes)}).to_numpy()
    k = args.blocks
    print(f"{len(y)} frames, {X.shape[1]} features, {len(classes)} classes, "
          f"{meta['sequence'].nunique()} sequences -> {k} time-block folds")

    oof = np.full(len(y), -1)
    fold_rows = []
    for fold, (tr, te) in enumerate(vicos_data.time_block_folds(meta, k, args.purge)):
        tr = tr[:: args.train_stride]
        t0 = time.time()
        model = make_model(args.model, len(classes))
        model.fit(X[tr], y[tr])
        oof[te] = model.predict(X[te])
        fold_rows.append({
            "fold": fold, "n_train": int(len(tr)), "n_test": int(len(te)),
            "test_classes_unseen_in_train": sorted(set(classes[c] for c in np.unique(y[te])) -
                                                   set(classes[c] for c in np.unique(y[tr]))),
            "macro_f1": f1_score(y[te], oof[te], average="macro",
                                 labels=np.unique(y[te])),
            "balanced_acc": balanced_accuracy_score(y[te], oof[te]),
            "seconds": round(time.time() - t0, 1)})
        print(fold_rows[-1])

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    summary = {
        "model": args.model, "split": f"time-block folds: {k} blocks per sequence, all cameras together, purge={args.purge} frames",
        "n_frames": int(len(y)), "n_features": int(X.shape[1]),
        "pooled_macro_f1": f1_score(y, oof, average="macro"),
        "pooled_balanced_acc": balanced_accuracy_score(y, oof),
        "pooled_accuracy": float((y == oof).mean()),
        "majority_class_baseline_acc": float(np.bincount(y).max() / len(y)),
        "per_fold": fold_rows}
    (out / f"metrics_{args.model}{args.tag}.json").write_text(json.dumps(summary, indent=2, default=float))
    rep = classification_report(y, oof, target_names=classes, output_dict=True, zero_division=0)
    pd.DataFrame(rep).T.round(3).to_csv(out / f"per_class_{args.model}{args.tag}.csv")

    cm = confusion_matrix(y, oof, normalize="true")
    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=60, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    for i in range(len(classes)):
        for j in range(len(classes)):
            if cm[i, j] >= 0.05:
                ax.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center", fontsize=7,
                        color="white" if cm[i, j] > 0.5 else "black")
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"VICOS positions, {args.model}, out-of-fold (rows sum to 1)")
    fig.colorbar(im); fig.tight_layout()
    fig.savefig(out / f"confusion_{args.model}{args.tag}.png", dpi=130)
    print(json.dumps({k_: v for k_, v in summary.items() if k_ != "per_fold"}, indent=2, default=float))


if __name__ == "__main__":
    main()
