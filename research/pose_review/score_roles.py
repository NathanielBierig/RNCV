"""Score roles.py against roles_gt.csv (48 attempt frames + negative frames outside the attempts).

    python -I research/pose_review/score_roles.py [--render]
Neck located = predicted defender neck within 1 grid cell (12x8 grid over the frame) of the GT cell centre.
Writes data/pose_review/roles_pred.csv and, with --render, data/pose_review/roles_fail.jpg.
"""
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import roles  # noqa: E402
from common import OUT, read_frames  # noqa: E402

HERE = Path(__file__).resolve().parent
COLS = "ABCDEFGHIJKL"


def cell_xy(cell, W, H):
    return np.array([(COLS.index(cell[0]) + 0.5) * W / 12, (int(cell[1:]) - 0.5) * H / 8])


def predict(e):
    frames = read_frames(e)
    per = []
    for s, f in zip(e["seq"], frames):
        c = list(zip(*s["rtmo"])) + list(zip(s["v1"][0], s["v1"][1]))
        per.append(roles.frame_roles(c, f))
    return per[-1], roles.smooth(per, e["fps"] / 2), frames[-1].shape


def rate(y, p):
    y, p = np.asarray(y, bool), np.asarray(p, bool)
    return f"{(p & y).sum()}/{y.sum()}" if y.sum() else "-"


def summarize(df, tag):
    att = df[df.pos != "neg"]
    neg = df[df.pos == "neg"]
    g = att[att.neck_cell.notna()]
    out = {"subset": tag, "frames": len(att),
           "neck located (1 cell)": f"{int(g.neck_ok.sum())}/{len(g)}",
           "neck located (1.5 cells)": f"{int(g.neck_ok15.sum())}/{len(g)}",
           "arm: recall on GT Y": rate(att.arm_across_neck == "Y", att.arm),
           "arm: fires on GT unclear": rate(att.arm_across_neck == "U", att.arm),
           "arm: false alarms on negatives": rate(neg.arm_across_neck == "N", neg.arm) if len(neg) else "-",
           "under_chin agreement": f"{(att[(att.arm_position.notna()) & att.arm].arm_position == att[(att.arm_position.notna()) & att.arm].pred_pos).sum()}/{((att.arm_position.notna()) & att.arm).sum()}",
           "hooks: recall on GT Y": rate(att.hooks_gt == "Y", att.hooks),
           "hooks: false alarms on negatives": rate(neg.hooks_gt == "N", neg.hooks) if len(neg) else "-",
           "back: correct (GT Y/N)": f"{((df.back_control == 'Y') & df.back | (df.back_control == 'N') & ~df.back).sum()}/{df.back_control.isin(['Y', 'N']).sum()}"}
    return out


def main():
    gt = pd.read_csv(HERE / "roles_gt.csv", dtype=str)
    view = pd.read_csv(HERE / "eval.csv")[["row", "pos", "view"]].drop_duplicates()
    cache = pickle.load(open(OUT / "cache.pkl", "rb"))
    if (OUT / "cache_neg.pkl").exists():
        cache += pickle.load(open(OUT / "cache_neg.pkl", "rb"))
    rows, keep = [], {}
    for e in cache:
        g = gt[(gt.row == str(e["row"])) & (gt.pos == e["pos"])]
        if g.empty:
            continue
        g = g.iloc[0]
        raw, sm, shp = predict(e)
        for mode, r in (("raw", raw), ("smoothed", sm)):
            ok = ok15 = np.nan
            if isinstance(g.neck_cell, str) and g.neck_cell:
                t = cell_xy(g.neck_cell, shp[1], shp[0])
                d = None if r["neck"] is None else max(abs(r["neck"][0] - t[0]) / (shp[1] / 12), abs(r["neck"][1] - t[1]) / (shp[0] / 8))
                ok, ok15 = d is not None and d <= 1.0, d is not None and d <= 1.5
            rows.append(dict(row=e["row"], pos=e["pos"], mode=mode, neck_cell=g.neck_cell, neck_ok=ok, neck_ok15=ok15,
                             arm_across_neck=g.arm_across_neck, arm=r["arm"], arm_position=g.arm_position, pred_pos=r["arm_position"],
                             hooks_gt=g.hooks, hooks=r["hooks"], back_control=g.back_control, back=r["back"],
                             n_anchor=r["n_anchor"], neck_x=None if r["neck"] is None else round(float(r["neck"][0])),
                             neck_y=None if r["neck"] is None else round(float(r["neck"][1]))))
        keep[(e["row"], e["pos"])] = (e, raw)
        print(e["row"], e["pos"], raw["arm"], sm["arm"], flush=True)
    df = pd.DataFrame(rows)
    df = df.merge(view, on=["row", "pos"], how="left")
    df["neck_ok"], df["neck_ok15"] = df.neck_ok.astype(float), df.neck_ok15.astype(float)
    df.to_csv(OUT / "roles_pred.csv", index=False)
    res = []
    for mode in ("raw", "smoothed"):
        d = df[df["mode"] == mode]
        res.append({"mode": mode, **summarize(d, "all 48")})
        res.append({"mode": mode, **summarize(d[(d.view == "ok") | (d.pos == "neg")], "23 clean")})
    print(pd.DataFrame(res).T.to_string())
    if "--render" in sys.argv:
        render_fail(df[df["mode"] == "raw"], keep)


def render_fail(df, keep):
    """Clean frame with GT neck cell (green box), predicted neck (red dot); failures + a few successes."""
    tiles = []
    att = df[(df.pos != "neg") & df.neck_cell.notna()]
    pick = list(att[att.neck_ok == 0].head(6).itertuples()) + list(att[att.neck_ok == 1].head(2).itertuples())  # noqa: E712
    for r in pick:
        e, raw = keep[(r.row, r.pos)]
        img = cv2.imread(str(OUT / "frames" / f"r{r.row:02d}_{r.pos}.jpg"))
        H, W = img.shape[:2]
        c = cell_xy(r.neck_cell, W, H)
        cv2.rectangle(img, tuple((c - [W / 24, H / 16]).astype(int)), tuple((c + [W / 24, H / 16]).astype(int)), (0, 255, 0), 4)
        if raw["neck"] is not None:
            cv2.circle(img, tuple(raw["neck"].astype(int)), 18, (0, 0, 255), -1)
        im = cv2.resize(img, (480, int(480 * H / W)))
        cv2.putText(im, f"r{r.row} {r.pos} {'OK' if r.neck_ok else 'MISS'} arm={r.arm}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 2)
        tiles.append(cv2.resize(im, (480, 270)))
    while len(tiles) % 4:
        tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(str(OUT / "roles_fail.jpg"), np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]))


if __name__ == "__main__":
    main()
