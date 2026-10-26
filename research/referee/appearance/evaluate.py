"""Score referee-detection methods on the hand-labeled eval set.

    python -I research/referee/appearance/evaluate.py

Needs data/referee/dets (eval/extract.py) and data/referee/feats (features.py).
Per-person metrics use people that survive select()'s crowd rule (not small_box).
Frame metric plugs each score into a select() variant (two_fighters rules, but
people with referee score > 0.5 are dropped before the overlap-pair rule).
Methods that learn anything are trained leave-one-clip-out (train on 2 clips,
test on the 3rd), so no clip is scored by a model that saw it.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402

CLIPS = ["gsp_bisping", "pantoja_asakura_r2", "sterling_sandhagen"]
CLOTH = ["torso_skin", "uarm_skin", "legs_skin", "torso_dark", "uarm_dark", "legs_dark"]
REF_THR = 0.5


def load():
    D = {}
    for c in CLIPS:
        z = np.load(ROOT / f"data/referee/dets/{c}.npz", allow_pickle=True)
        f = np.load(ROOT / f"data/referee/feats/{c}.npz")
        frames = [int(i) for i in z["frame_idx"]]
        dets = {fr: (k, s) for fr, k, s in zip(frames, z["kpts"], z["scores"])}
        key = {(int(a), int(b)): n for n, (a, b) in enumerate(zip(f["frame"], f["person_idx"]))}
        D[c] = dict(frames=frames, dets=dets, key=key, f={k: f[k] for k in f.files})
    labels = {}
    for r in csv.DictReader(open(ROOT / "research/referee/eval/labels.csv")):
        labels[(r["clip"], int(r["frame"]), int(r["person_idx"]))] = (r["label"], r["small_box"] == "1")
    return D, labels


def small_mask(K, S):
    a = np.array([tf.box_area(k, s) for k, s in zip(K, S)])
    return a < 0.15 * max(a.max(), 1) if len(a) else np.zeros(0, bool)


def kbox(k, s):
    return tf._box(k, s)


# ---------------------------------------------------------------- tracking (3c)
def build_tracks(d, max_gap=3):
    """IoU + CLIP-embedding tracker over all stride-5 frames. Returns {(frame, idx): track_id}."""
    emb = d["f"]["emb"].astype(np.float32)
    tid, active, nxt = {}, [], 0          # active: [track_id, box, emb, last_t]
    for t, fr in enumerate(d["frames"]):
        K, S = d["dets"][fr]
        if not len(S):
            continue
        sm = small_mask(K, S)
        cand = [j for j in range(len(S)) if not sm[j]]
        active = [a for a in active if t - a[3] <= max_gap]
        boxes = {j: kbox(K[j], S[j]) for j in cand}
        es = {j: emb[d["key"][(fr, j)]] for j in cand}
        cost = np.full((len(cand), len(active)), 9.0)
        for x, j in enumerate(cand):
            for y, a in enumerate(active):
                iou = tf._iou(boxes[j], a[1])
                if iou > 0.1:
                    cost[x, y] = (1 - iou) + 2 * (1 - float(es[j] @ a[2]))
        used = set()
        if len(cand) and len(active):
            for x, y in zip(*linear_sum_assignment(cost)):
                if cost[x, y] < 1.6:
                    j = cand[x]
                    a = active[y]
                    tid[(fr, j)] = a[0]
                    a[1], a[2], a[3] = boxes[j], 0.7 * a[2] + 0.3 * es[j], t
                    a[2] /= np.linalg.norm(a[2])
                    used.add(j)
        for j in cand:
            if j not in used:
                tid[(fr, j)] = nxt
                active.append([nxt, boxes[j], es[j].copy(), t]); nxt += 1
    return tid


def track_vote(d, tid, score):
    """Replace each detection's score with its track's mean score."""
    acc = defaultdict(list)
    for (fr, j), t in tid.items():
        acc[t].append(score[d["key"][(fr, j)]])
    mean = {t: float(np.mean(v)) for t, v in acc.items()}
    out = score.copy()
    for (fr, j), t in tid.items():
        out[d["key"][(fr, j)]] = mean[t]
    return out


# ---------------------------------------------------------------- selection
def select_ref(K, S, ref):
    """two_fighters.select with a referee score: returns kept person indices."""
    if not len(S):
        return []
    order = np.argsort(-S.mean(1))
    sm = small_mask(K, S)
    keep = []
    for i in order:
        if sm[i]:
            continue
        k, s = K[i], S[i]
        scale = np.sqrt(max(tf.box_area(k, s), 1.0))
        if any(tf._same_body(k, s, K[j], S[j], scale) for j in keep):
            continue
        keep.append(i)
    if ref is not None:
        keep = [i for i in keep if ref[i] <= REF_THR]
    if len(keep) > 2:
        boxes = {i: kbox(K[i], S[i]) for i in keep}
        pos = {i: p for p, i in enumerate(keep)}
        best = max(((a, b) for x, a in enumerate(keep) for b in keep[x + 1:]),
                   key=lambda ab: (tf._iou(boxes[ab[0]], boxes[ab[1]]), -pos[ab[0]] - pos[ab[1]]))
        keep = list(best)
    return [int(i) for i in keep]


# ---------------------------------------------------------------- methods
def loco_fit(D, labels, featfn, C=1.0):
    """Leave-one-clip-out logistic regression on labeled non-small people -> scores for all dets."""
    X, y, cl = [], [], []
    for c in CLIPS:
        d = D[c]
        for (cc, fr, j), (lab, small) in labels.items():
            if cc != c or small or lab not in ("fighter", "referee", "duplicate"):
                continue
            X.append(featfn(d, d["key"][(fr, j)])); y.append(lab == "referee"); cl.append(c)
    X, y, cl = np.array(X), np.array(y), np.array(cl)
    out = {}
    for c in CLIPS:
        m = LogisticRegression(C=C, max_iter=2000, class_weight="balanced").fit(X[cl != c], y[cl != c])
        d = D[c]
        allX = np.array([featfn(d, n) for n in range(len(d["f"]["frame"]))])
        out[c] = m.predict_proba(allX)[:, 1]
    return out


def cloth_vec(d, n):
    v = np.array([d["f"][k][n] for k in CLOTH], float)
    miss = np.isnan(v).astype(float)
    return np.r_[np.nan_to_num(v, nan=0.5), miss[:3]]


def emb_vec(d, n):
    return d["f"]["emb"][n].astype(np.float32)


def evaluate(D, labels, scores):
    """scores: {clip: array over all dets} or None (baseline). Returns metrics dict."""
    y, s = [], []
    both, both_n, refk, refk_n, lostF = 0, 0, 0, 0, 0
    per_clip = {}
    for c in CLIPS:
        d = D[c]
        fr_lab = defaultdict(dict)
        for (cc, fr, j), v in labels.items():
            if cc == c:
                fr_lab[fr][j] = v
        cb = cn = 0
        for fr, lab in fr_lab.items():
            K, S = d["dets"][fr]
            ref = None if scores is None else np.array([scores[c][d["key"][(fr, j)]] for j in range(len(S))])
            if ref is not None:
                for j, (l, small) in lab.items():
                    if not small:
                        y.append(l == "referee"); s.append(ref[j])
            kept = select_ref(K, S, ref)
            kl = [lab[j][0] for j in kept]
            nF = sum(1 for l, sm in lab.values() if l == "fighter" and not sm)
            if nF >= 2:
                ok = len(kept) == 2 and all(l == "fighter" for l in kl)
                both += ok; both_n += 1; cb += ok; cn += 1
            if any(l == "referee" and not sm for l, sm in lab.values()):
                refk_n += 1; refk += "referee" in kl
            if ref is not None:
                lostF += sum(1 for j, (l, sm) in lab.items() if l == "fighter" and not sm and ref[j] > REF_THR)
        per_clip[c] = f"{cb}/{cn}"
    m = {"both": f"{both}/{both_n} ({100 * both / both_n:.0f}%)",
         "ref_kept": f"{refk}/{refk_n} ({100 * refk / refk_n:.0f}%)", "per_clip_both": per_clip}
    if scores is not None:
        y, s = np.array(y), np.array(s)
        pred = s > REF_THR
        tp = (pred & y).sum()
        m.update(auc=roc_auc_score(y, s), precision=tp / max(pred.sum(), 1), recall=tp / y.sum(),
                 fighters_flagged=lostF, n_ref=int(y.sum()), n=len(y))
    return m


def main():
    D, labels = load()
    tids = {c: build_tracks(D[c]) for c in CLIPS}
    gi = list(D[CLIPS[0]]["f"]["groups"]).index("referee")
    base = {
        "a. CLIP zero-shot": {c: D[c]["f"]["clip_p"][:, gi] for c in CLIPS},
        "a'. CLIP linear probe (LOCO)": loco_fit(D, labels, emb_vec, C=0.5),
        "b. Skin rule (referee.py)": {c: D[c]["f"]["rule"] for c in CLIPS},
        "b'. Skin features + logistic (LOCO)": loco_fit(D, labels, cloth_vec),
    }
    methods = {"Baseline: overlap pair (current select)": None}
    for name, sc in base.items():
        methods[name] = sc
        methods[name + " + track vote"] = {c: track_vote(D[c], tids[c], sc[c]) for c in CLIPS}
    combo = {c: 0.5 * base["a. CLIP zero-shot"][c] + 0.5 * base["b. Skin rule (referee.py)"][c] for c in CLIPS}
    methods["a+b average"] = combo
    methods["a+b average + track vote"] = {c: track_vote(D[c], tids[c], combo[c]) for c in CLIPS}
    rows = []
    for name, sc in methods.items():
        m = evaluate(D, labels, sc)
        rows.append((name, m))
        print(name, m, flush=True)
    np.save(ROOT / "data/referee/eval_results.npy", np.array(rows, dtype=object), allow_pickle=True)
    np.savez(ROOT / "data/referee/method_scores.npz",
             **{f"{n}|{c}": v[c] for n, v in methods.items() if v is not None for c in CLIPS})
    print("\n| Method | AUC | Precision | Recall | Fighters flagged | Both fighters kept | Referee kept | per clip (gsp/pantoja/sterling) |")
    print("|---|---|---|---|---|---|---|---|")
    for name, m in rows:
        if "auc" in m:
            mid = f"{m['auc']:.2f} | {m['precision']:.2f} | {m['recall']:.2f} | {m['fighters_flagged']}"
        else:
            mid = "– | – | – | –"
        pc = " / ".join(m["per_clip_both"][c] for c in CLIPS)
        print(f"| {name} | {mid} | {m['both']} | {m['ref_kept']} | {pc} |")


if __name__ == "__main__":
    main()
