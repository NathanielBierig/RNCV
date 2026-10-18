"""Critic's checks on the Phase 2 VICOS classifier (read-only use of src/).
1. Shortcut test: VICOS position is confounded with sequence (Back only in seq 5).
   Train on time-block folds as build-phase2 does, then look at the few 'standing'
   frames in sequences 0-3: are they predicted as that sequence's drilled position?
   Also: can the features predict the *sequence* from standing frames alone?
2. Identity-swap test: swap pose1<->pose2 and label suffix 1<->2 at test time.
   A tracker on UFC footage gives arbitrary IDs, so the model must survive this.
Run: python -I -B -W ignore research/critique/shortcut_check.py
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGB
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold
import features, vicos_data

meta, poses = vicos_data.load()
X, _ = features.build(poses)
Xs, _ = features.build(poses[:, ::-1].copy())
classes = sorted(meta.position.unique()); idx = {c: i for i, c in enumerate(classes)}
sw = lambda c: c[:-1] + {"1": "2", "2": "1"}[c[-1]] if c[-1] in "12" else c
y = meta.position.map(idx).to_numpy(); ys = meta.position.map(lambda c: idx[sw(c)]).to_numpy()
seq = meta.sequence.to_numpy()
mk = lambda: HGB(max_iter=150, learning_rate=0.1, class_weight="balanced", random_state=0)

oof = np.full(len(y), -1); oofs = np.full(len(y), -1)
for k, (tr, te) in enumerate(vicos_data.time_block_folds(meta)):
    m = mk().fit(X[tr[::4]], y[tr[::4]])
    oof[te] = m.predict(X[te]); oofs[te] = m.predict(Xs[te])
    print(f"fold {k}: macroF1={f1_score(y[te], oof[te], average='macro'):.3f} "
          f"swapped-input macroF1={f1_score(ys[te], oofs[te], average='macro'):.3f}", flush=True)
done = oof >= 0
print(f"POOLED time-block macroF1={f1_score(y[done], oof[done], average='macro'):.3f}  "
      f"identity-swapped={f1_score(ys[done], oofs[done], average='macro'):.3f}")
back = np.isin(y, [idx['back1'], idx['back2']]); pb = np.isin(oof, [idx['back1'], idx['back2']])
print(f"Back recall (merged) {(back & pb & done).sum() / (back & done).sum():.3f}; "
      f"back1/back2 side correct among Back hits {(oof[back & pb] == y[back & pb]).mean():.3f}; "
      f"swapped side correct {(oofs[back & pb] == ys[back & pb]).mean():.3f}")

st = (meta.position == "standing").to_numpy() & done
print("\nStanding frames: OOF predictions by sequence")
print(pd.crosstab(seq[st], np.array(classes)[oof[st]]).to_string())

# sequence-ID probe on standing frames only (grouped by time block of 300 frames)
s_idx = np.where((meta.position == "standing").to_numpy())[0]
g = seq[s_idx] * 1000 + meta.frame.to_numpy()[s_idx] // 300
acc = []
for tr, te in GroupKFold(5).split(s_idx, groups=g):
    m = HGB(max_iter=100, random_state=0).fit(X[s_idx[tr]], seq[s_idx[tr]])
    acc.append((m.predict(X[s_idx[te]]) == seq[s_idx[te]]).mean())
print(f"\nSequence-ID from standing-frame pose features: acc={np.mean(acc):.3f} "
      f"(chance ~{pd.Series(seq[s_idx]).value_counts(normalize=True).max():.3f}, majority)")
