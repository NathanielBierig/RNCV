"""Phase 2 baseline: 18-class BJJ position classifier on VICOS keypoints (CPU).

Splits are group-aware: each fold holds out one contiguous time block of every
sparring sequence, across all cameras, with a purge buffer around it (see
vicos_data.time_block_folds). Random frame-level splits are never used, because
neighbouring frames and other camera views of the same moment would leak.

Usage:
    python -I src/train_baseline.py --model gbm       # gradient boosting (default)
    python -I src/train_baseline.py --model mlp       # small MLP for comparison
    python -I src/train_baseline.py --swap-aug --tag _swapaug   # athlete-order augmentation

Every run also reports the "swap" macro-F1: the same test frames with pose1/pose2
swapped and the label suffix 1<->2 swapped. A model that uses geometry, not
athlete identity or order, scores the same on both (critique #13). Tracker IDs
on UFC footage are arbitrary, so this matters.
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


def swap_label_index(classes):
    """Index of each class after swapping athletes: mount1 <-> mount2; standing stays."""
    idx = {c: i for i, c in enumerate(classes)}
    return np.array([idx.get(c[:-1] + {"1": "2", "2": "1"}[c[-1]], i) if c[-1] in "12" else i
                     for i, c in enumerate(classes)])


def fold_macro_f1(y_true, y_pred):
    # classes present in truth OR predictions, so false positives into classes absent
    # from this block still count (critique #18); classes absent from both are skipped
    return f1_score(y_true, y_pred, average="macro", zero_division=0,
                    labels=np.union1d(y_true, y_pred))


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
    ap.add_argument("--swap-aug", action="store_true",
                    help="train on each frame twice: as-is and with athletes + label suffix swapped")
    args = ap.parse_args()

    meta, poses = vicos_data.load(args.annotations)
    X, names = features.build(poses)
    X_sw, _ = features.build(poses[:, ::-1])          # athletes swapped
    classes = sorted(meta["position"].unique())
    y = meta["position"].map({c: i for i, c in enumerate(classes)}).to_numpy()
    sw = swap_label_index(classes)
    base = np.array([c.rstrip("12") for c in classes])  # 10 role-free positions
    k = args.blocks
    print(f"{len(y)} frames, {X.shape[1]} features, {len(classes)} classes, "
          f"{meta['sequence'].nunique()} sequences -> {k} time-block folds")

    oof = np.full(len(y), -1)
    oof_sw = np.full(len(y), -1)
    fold_rows = []
    for fold, (tr, te) in enumerate(vicos_data.time_block_folds(meta, k, args.purge)):
        tr = tr[:: args.train_stride]
        t0 = time.time()
        model = make_model(args.model, len(classes))
        if args.swap_aug:
            model.fit(np.vstack([X[tr], X_sw[tr]]), np.concatenate([y[tr], sw[y[tr]]]))
        else:
            model.fit(X[tr], y[tr])
        oof[te] = model.predict(X[te])
        oof_sw[te] = model.predict(X_sw[te])
        fold_rows.append({
            "fold": fold, "n_train": int(len(tr)), "n_test": int(len(te)),
            "test_classes_unseen_in_train": sorted(set(classes[c] for c in np.unique(y[te])) -
                                                   set(classes[c] for c in np.unique(y[tr]))),
            "macro_f1": fold_macro_f1(y[te], oof[te]),
            "swap_macro_f1": fold_macro_f1(sw[y[te]], oof_sw[te]),
            "balanced_acc": balanced_accuracy_score(y[te], oof[te]),
            "seconds": round(time.time() - t0, 1)})
        print(fold_rows[-1])

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    summary = {
        "model": args.model, "swap_aug": args.swap_aug, "annotations": Path(args.annotations).name,
        "split": f"time-block folds: {k} blocks per sequence, all cameras together, purge={args.purge} frames",
        "n_frames": int(len(y)), "n_features": int(X.shape[1]),
        "pooled_macro_f1": f1_score(y, oof, average="macro"),
        "pooled_swap_macro_f1": f1_score(sw[y], oof_sw, average="macro"),
        "pooled_macro_f1_10_positions_roles_merged": f1_score(base[y], base[oof], average="macro"),
        "pooled_balanced_acc": balanced_accuracy_score(y, oof),
        "pooled_accuracy": float((y == oof).mean()),
        "majority_class_baseline_acc": float(np.bincount(y).max() / len(y)),
        "per_fold": fold_rows}
    (out / f"metrics_{args.model}{args.tag}.json").write_text(json.dumps(summary, indent=2, default=float))
    pd.DataFrame({"row": np.arange(len(y)), "video": meta["video"], "frame": meta["frame"],
                  "true": np.array(classes)[y], "pred": np.array(classes)[oof],
                  "pred_swapped_input": np.array(classes)[oof_sw]}
                 ).to_csv(out / f"oof_{args.model}{args.tag}.csv", index=False)
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
