"""Compare referee-removal variants from the cached model outputs (cache_dets.py first).

    python -I research/referee/detector/evaluate.py [--evidence]

Variants (all end in src/two_fighters.select + TwoSlotTracker, stride 3, 0.5 s gap fill):
  baseline   RTMO-m people (score 0.3)                   -> select
  topdown    fight-judge boxes (conf >= 0.25) -> RTMPose-m -> select
  hybrid     RTMO people, drop IoU < 0.3 with every fight-judge box (conf >= 0.25) -> select
  hybrid10   same, fight-judge boxes at conf >= 0.10
Prints a markdown table; --evidence also writes side-by-side frames to
data/referee/detector/evidence/ (local only). If research/referee/eval/labels.csv exists,
also scores referee-kept / fighter-dropped per variant on its frames.
"""
import csv
import glob
import pickle
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
import two_fighters as tf  # noqa: E402
from fighter_boxes import gate_people, iou, person_box, select_fighters  # noqa: E402

OUT = ROOT / "data" / "referee" / "detector"
STRIDE = 3


def people(fr, variant):
    """Candidate people (kpts, scores) for one cached frame under a variant."""
    rk, rs = fr["rtmo_k"], fr["rtmo_s"]
    if variant == "baseline":
        return rk, rs
    if variant == "topdown":
        return fr["td_k"], fr["td_s"]
    conf, mode, thr = {"hybrid": (0.25, "iou", 0.3), "hybrid10": (0.10, "iou", 0.3),
                       "hybrid_ioa": (0.25, "ioa", 0.6)}[variant]
    return gate_people(rk, rs, fr["fj_boxes"][fr["fj_conf"] >= conf], thr, mode)


VARIANTS = ["baseline", "topdown", "hybrid", "hybrid10", "hybrid_ioa", "rank", "rank0"]


def choose(fr, variant):
    """(kept kpts, kept scores, dropped, counts) for one frame."""
    if variant.startswith("rank"):
        fb = fr["fj_boxes"][fr["fj_conf"] >= 0.25]
        return select_fighters(fr["rtmo_k"], fr["rtmo_s"], fb, 0.2 if variant == "rank" else 0.0)
    return tf.select(*people(fr, variant))


def track_metrics(cache, variant):
    frames = cache["frames"]
    idx = sorted(i for i in frames if i % STRIDE == 0)
    tracker = tf.TwoSlotTracker(cache["fps"] / STRIDE, 0.5)
    st, upper, t = [], [], []
    for i in idx:
        fr = frames[i]
        ks, ss, _, _ = choose(fr, variant)
        _, states = tracker.update(ks, ss)
        st.append(states)
        upper.append(len(ss) == 2 and all(tf.upper_ok(x) for x in ss))
        t.append({"baseline": fr["t_rtmo"], "topdown": fr["t_fj"] + fr["t_td"]}.get(
            variant, fr["t_rtmo"] + fr["t_fj"]))
    st = np.array(st)
    return {"seen": 100 * (st == tf.SEEN).all(1).mean(),
            "seen_filled": 100 * (st != tf.MISSING).all(1).mean(),
            "upper": 100 * np.mean(upper), "fps": 1 / np.mean(t[1:]), "n": len(idx)}


def detector_stats(cache):
    fr = [f for i, f in cache["frames"].items() if i % STRIDE == 0]
    n = np.array([(f["fj_conf"] >= 0.25).sum() for f in fr])
    return {"fj0": 100 * (n == 0).mean(), "fj1": 100 * (n == 1).mean(),
            "fj2": 100 * (n == 2).mean(), "fj3": 100 * (n >= 3).mean()}


def kept_boxes(fr, variant):
    ks, ss, _, _ = choose(fr, variant)
    return [person_box(a, b) for a, b in zip(ks, ss)]


def label_eval(caches):
    """Score on research/referee/eval/labels.csv (ref-appearance session), same metrics as
    appearance/evaluate.py: "both kept" = the 2 kept people are both labeled fighter, among
    frames with >= 2 non-small fighters; "referee kept" among frames with a non-small referee.
    Kept people are matched to labeled boxes by IoU (best match >= 0.5; top-down skeletons are
    new detections, so >= 0.3 and unmatched ones are counted separately)."""
    path = ROOT / "research" / "referee" / "eval" / "labels.csv"
    if not path.exists():
        return None
    by_frame = {}
    for r in csv.DictReader(open(path, newline="")):
        box = np.array([float(r[c]) for c in ("x0", "y0", "x1", "y1")])
        by_frame.setdefault((r["clip"], int(r["frame"])), []).append((box, r["label"], r["small_box"] == "1"))
    res = {v: dict(both=0, both_n=0, ref=0, ref_n=0, fdrop=0, f_n=0, unmatched=0, per_clip={}) for v in VARIANTS}
    for (clip, f), gt in by_frame.items():
        if clip not in caches or f not in caches[clip]["frames"]:
            continue
        fr = caches[clip]["frames"][f]
        nF = sum(1 for _, l, sm in gt if l == "fighter" and not sm)
        has_ref = any(l == "referee" and not sm for _, l, sm in gt)
        for v in VARIANTS:
            kb, R = kept_boxes(fr, v), res[v]
            mthr = 0.3 if v == "topdown" else 0.5
            labs = []
            for b in kb:
                j = max(range(len(gt)), key=lambda j: iou(b, gt[j][0]))
                labs.append(gt[j][1] if iou(b, gt[j][0]) >= mthr else "none")
            R["unmatched"] += labs.count("none")
            pc = R["per_clip"].setdefault(clip, [0, 0])
            if nF >= 2:
                ok = len(kb) == 2 and all(l == "fighter" for l in labs)
                R["both"] += ok; R["both_n"] += 1; pc[0] += ok; pc[1] += 1
                for g, l, sm in gt:
                    if l == "fighter" and not sm:
                        R["f_n"] += 1
                        R["fdrop"] += not any(iou(b, g) >= mthr for b in kb)
            if has_ref:
                R["ref_n"] += 1; R["ref"] += "referee" in labs
    return res


def evidence(caches, frames_by_clip):
    """2x2: baseline, hybrid / hybrid_ioa, topdown. Green = kept, red = dropped, blue = fight-judge box."""
    ev = OUT / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    for clip, fl in frames_by_clip.items():
        cap = cv2.VideoCapture(str(ROOT / "data" / "clips" / f"{clip}.mp4"))
        for f in fl:
            if f not in caches[clip]["frames"]:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, f)
            ok, img = cap.read()
            if not ok:
                continue
            fr = caches[clip]["frames"][f]
            panels = []
            for v in ("baseline", "hybrid", "hybrid_ioa", "topdown"):
                p = img.copy()
                if v != "baseline":
                    for b, c in zip(fr["fj_boxes"], fr["fj_conf"]):
                        if c >= 0.25:
                            cv2.rectangle(p, tuple(map(int, b[:2])), tuple(map(int, b[2:])), (255, 120, 0), 3)
                            cv2.putText(p, f"{c:.2f}", (int(b[0]), int(b[1]) - 8), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 120, 0), 3)
                k, s = people(fr, v)
                ks, ss, dropped, _ = tf.select(k, s)
                cand = [(a, b) for a, b in zip(fr["rtmo_k"], fr["rtmo_s"])] if v != "topdown" else list(zip(k, s))
                for a, b in cand:
                    kept = any(np.allclose(a, x) for x in ks)
                    col = (0, 220, 0) if kept else (0, 0, 255)
                    for x, y in a[b >= tf.THR].astype(int):
                        cv2.circle(p, (int(x), int(y)), 7, col, -1)
                cv2.putText(p, f"{v} {clip} {f}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 4)
                panels.append(cv2.resize(p, (960, 540)))
            cv2.imwrite(str(ev / f"{clip}_{f}.jpg"), np.vstack([np.hstack(panels[:2]), np.hstack(panels[2:])]), [cv2.IMWRITE_JPEG_QUALITY, 85])
        cap.release()


def main():
    caches = {}
    for p in sorted(glob.glob(str(OUT / "cache" / "*.pkl"))):
        caches[Path(p).stem] = pickle.load(open(p, "rb"))
    print("| Clip | Variant | 2 tracked (seen) | 2 tracked (seen or filled) | 2 kept, both upper OK | CPU fps |")
    print("|---|---|---|---|---|---|")
    for clip, c in caches.items():
        for v in VARIANTS:
            m = track_metrics(c, v)
            print(f"| {clip} | {v} | {m['seen']:.0f}% | {m['seen_filled']:.0f}% | {m['upper']:.0f}% | {m['fps']:.1f} |")
    print()
    for clip, c in caches.items():
        print(clip, "fight-judge boxes >=0.25 (0/1/2/3+ %):", {k: round(v) for k, v in detector_stats(c).items()})
    le = label_eval(caches)
    if le:
        pct = lambda a, n: f"{a}/{n} ({100 * a / max(n, 1):.0f}%)"
        print("\n| Variant | Both fighters kept | per clip (gsp / pantoja / sterling) | Referee kept | Fighters dropped | Kept but unmatched |")
        print("|---|---|---|---|---|---|")
        for v, R in le.items():
            pcs = " / ".join(f"{a}/{n}" for a, n in (R["per_clip"].get(c, [0, 0]) for c in sorted(R["per_clip"])))
            print(f"| {v} | {pct(R['both'], R['both_n'])} | {pcs} | {pct(R['ref'], R['ref_n'])} | "
                  f"{pct(R['fdrop'], R['f_n'])} | {R['unmatched']} |")
    if "--evidence" in sys.argv:
        sel = {}
        for p in glob.glob(str(ROOT / "data/pose/select2/*_ref_*.jpg")):
            stem = Path(p).stem
            clip, f = stem.rsplit("_ref_", 1)
            sel.setdefault(clip, []).append(int(f))
        evidence(caches, sel)


if __name__ == "__main__":
    main()
