"""Load the VICOS BJJ annotations, map videos to sequences, and build time-block folds.

annotations.json is a list of records:
    {"image": "0000001", "frame": 1, "position": "mount2",
     "pose1": [[x, y, conf] * 17], "pose2": [[x, y, conf] * 17]}
pose1/pose2 are fixed athlete identities (the label suffix 1/2 refers to them),
so we never re-order them. Either pose may be missing.

Image ids are VVFFFFF: VV = video (00-15), FFFFF = frame. The 16 videos are
6 sparring sequences filmed by up to 3 phone cameras (checked: same-sequence
videos agree on the label at the same frame number 84-100% of the time,
unrelated videos 0.5%). Each sequence drills only a few positions, so
leave-one-sequence-out cannot work (test classes would be absent from
training). Instead, time_block_folds() holds out contiguous time blocks of
every sequence, keeping all cameras of the same moment in the same fold.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

N_JOINTS = 17
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "vicos" / "annotations.json"


def _pose(rec, key):
    p = rec.get(key)
    if not p or len(p) != N_JOINTS:
        return np.full((N_JOINTS, 3), np.nan, dtype=np.float32)
    return np.asarray(p, dtype=np.float32)


def load(path=DEFAULT_PATH):
    """Return (meta DataFrame, poses array of shape [N, 2, 17, 3])."""
    with open(path, encoding="utf-8") as f:
        recs = json.load(f)
    meta = pd.DataFrame({
        "image": [r["image"] for r in recs],
        "frame": [int(r["frame"]) for r in recs],
        "position": [r["position"] for r in recs],
    })
    poses = np.stack([np.stack([_pose(r, "pose1"), _pose(r, "pose2")]) for r in recs])
    meta["video"] = meta["image"].str[:2].astype(int)
    meta["sequence"] = meta["video"].map(VIDEO_TO_SEQUENCE)
    return meta, poses


VIDEO_TO_SEQUENCE = {v: s for s, vids in enumerate(
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10], [11, 12, 13], [14, 15]]) for v in vids}


def time_block_folds(meta, n_blocks=5, purge=300):
    """Yield (train_idx, test_idx). Fold k tests on time block k of every sequence.

    Blocks are cut on frame number per sequence, so all cameras of a moment
    share a block. Training frames within `purge` frames of the test block
    (any camera; ~10 s at 30 fps, also covers small camera clock offsets) are dropped.
    """
    frame = meta["frame"].to_numpy()
    seq = meta["sequence"].to_numpy()
    block = np.zeros(len(meta), dtype=int)
    edges = {}
    for s in np.unique(seq):
        m = seq == s
        e = np.linspace(frame[m].min(), frame[m].max() + 1, n_blocks + 1)
        edges[s] = e
        block[m] = np.clip(np.searchsorted(e, frame[m], side="right") - 1, 0, n_blocks - 1)
    for k in range(n_blocks):
        test = block == k
        near = np.zeros(len(meta), dtype=bool)
        for s, e in edges.items():
            m = seq == s
            near |= m & (frame >= e[k] - purge) & (frame < e[k + 1] + purge)
        yield np.where(~near)[0], np.where(test)[0]


if __name__ == "__main__":
    meta, poses = load(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH)
    print(f"{len(meta)} frames, {meta['video'].nunique()} videos, {meta['sequence'].nunique()} sequences")
    print(pd.crosstab(meta["position"], meta["sequence"]).to_string())
    missing = np.isnan(poses[:, :, 0, 0])
    print("frames missing pose1:", missing[:, 0].sum(), " missing pose2:", missing[:, 1].sum())
