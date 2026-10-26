"""Pose coverage inside each labeled RNC attempt -> reports/pose_attempts.md.

For every row of phase3_labels/labels.csv whose clip is in data/clips/ (`video_url`),
runs RTMO-m + two-fighter selection (referee filter) + tracking over the attempt window
[video_time_start, video_time_end] and reports, with the same measures as
reports/pose_smoke.md: % frames with both fighters tracked (seen, or filled <= 0.5 s)
and % frames where both upper bodies are OK (>= 5 of 7 upper-body joints).
Read-only on labels.csv.

    python -I src/pose_attempts.py            # stride 2
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
import two_fighters as tf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RTMO_M = ("https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
          "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip")
GATE = 60.0   # PLAN 2b gate: >= 60% usable frames during back control


HEAD = [0, 1, 2, 3, 4]   # nose, eyes, ears
L_SH, R_SH = 5, 6


def rnc_ok(poses, thr=tf.THR):
    """RNC-usable frame with fewer joints than 'both upper bodies OK': in back control the
    attacker is mostly hidden behind the defender, so we only need what an RNC is made of.
    Defender = the person with the more visible head+shoulders: head + both shoulders.
    Attacker = the other person: head + at least one shoulder, head close to the defender's head/neck
    (within 1.5 defender shoulder-widths). Both arms of the attacker may be hidden."""
    vis = lambda j: poses[j, :, 2] >= thr
    core = [vis(j)[HEAD].any() * 1 + vis(j)[[L_SH, R_SH]].sum() for j in range(2)]
    d, a = (0, 1) if core[0] >= core[1] else (1, 0)
    vd, va = vis(d), vis(a)
    if not (vd[HEAD].any() and vd[L_SH] and vd[R_SH] and va[HEAD].any() and (va[L_SH] or va[R_SH])):
        return False
    head = lambda j, v: poses[j, [h for h in HEAD if v[h]], :2].mean(0)
    sw = np.linalg.norm(poses[d, L_SH, :2] - poses[d, R_SH, :2]) + 1e-6
    return np.linalg.norm(head(a, va) - head(d, vd)) < 1.5 * sw


LOW = 0.1                            # low joint bar for the choker only
ARMS, LEGS = [7, 8, 9, 10], [13, 14, 15, 16]   # elbows, wrists / knees, ankles
L_HIP, R_HIP = 11, 12


def roles(poses, thr=tf.THR):
    vis = lambda j: poses[j, :, 2] >= thr
    core = [vis(j)[HEAD].any() * 1 + vis(j)[[L_SH, R_SH]].sum() for j in range(2)]
    return (0, 1) if core[0] >= core[1] else (1, 0)


def rnc_low(poses, thr=tf.THR, low=LOW):
    """Owner's idea: in back control the choker's torso is hidden, but the hands/forearms (at the neck)
    and a foot/calf (hooks, body triangle) usually show. Defender = anchor at the normal bar (head +
    one shoulder). Choker = the other tracked person at a LOW joint bar: counts if a wrist/elbow is
    within 1 defender shoulder-width of the defender's neck, or a knee/ankle within 1.5 of the
    defender's hips (or shoulders if the hips are hidden)."""
    d, a = roles(poses, thr)
    vd = poses[d, :, 2] >= thr
    if not (vd[HEAD].any() and (vd[L_SH] or vd[R_SH])):
        return False
    sh = [j for j in (L_SH, R_SH) if vd[j]]
    neck = poses[d, sh, :2].mean(0)
    sw = np.linalg.norm(poses[d, L_SH, :2] - poses[d, R_SH, :2]) if len(sh) == 2 else         np.linalg.norm(neck - poses[d, [h for h in HEAD if vd[h]], :2].mean(0)) * 2
    sw = max(sw, 1e-6)
    hips = [j for j in (L_HIP, R_HIP) if vd[j]]
    waist = poses[d, hips, :2].mean(0) if hips else neck
    va = poses[a, :, 2] >= low
    arm = any(va[j] and np.linalg.norm(poses[a, j, :2] - neck) < 1.0 * sw for j in ARMS)
    leg = any(va[j] and np.linalg.norm(poses[a, j, :2] - waist) < 1.5 * sw for j in LEGS)
    return bool(arm or leg)


def detect(model, frame, score_thr, nms_thr, fallback=None):
    """Pose + two-fighter selection. With a fallback (model, score_thr): if the main model keeps
    fewer than two fighters in this frame, the fallback model is tried and used if it keeps more."""
    kps, scs = model(frame, nms_thr=nms_thr, score_thr=score_thr)
    ks, ss, _, _ = tf.select(np.asarray(kps, np.float32).reshape(-1, 17, 2), np.asarray(scs, np.float32).reshape(-1, 17), frame)
    if fallback is not None and len(ks) < 2:
        fm, fthr = fallback
        k2, s2 = fm(frame, nms_thr=nms_thr, score_thr=fthr)
        k2, s2, _, _ = tf.select(np.asarray(k2, np.float32).reshape(-1, 17, 2), np.asarray(s2, np.float32).reshape(-1, 17), frame)
        if len(k2) > len(ks):
            return k2, s2, True
    return ks, ss, False


SKEL = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]


def draw_sample(frame, poses, path):
    """Defender blue (normal bar), choker red: solid joints >= normal bar, hollow joints = low-bar only."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img = frame.copy()
    d, a = roles(poses)
    for j, col, thr in ((d, (230, 120, 30), tf.THR), (a, (40, 40, 230), LOW)):
        k, c = poses[j, :, :2], poses[j, :, 2]
        for x, y in SKEL:
            if c[x] >= thr and c[y] >= thr:
                cv2.line(img, tuple(map(int, k[x])), tuple(map(int, k[y])), col, 2, cv2.LINE_AA)
        for q in range(17):
            if c[q] >= thr:
                cv2.circle(img, tuple(map(int, k[q])), 5, col, -1 if c[q] >= tf.THR else 2, cv2.LINE_AA)
    cv2.imwrite(str(path), cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2)))


def window_coverage(model, clip, t0, t1, stride, score_thr, nms_thr, fallback=None, sample=None):
    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000)
    tracker = tf.TwoSlotTracker(fps / stride)
    window_coverage.saved = False
    n = both = upper = rnc = fb = low = 0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok or cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 > t1:
            break
        if i % stride == 0:
            ks, ss, used_fb = detect(model, frame, score_thr, nms_thr, fallback)
            fb += used_fb
            poses, states = tracker.update(ks, ss)
            n += 1
            if sample is not None and not window_coverage.saved and cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 >= t0 + 2                     and all(st in (tf.SEEN, tf.FILLED) for st in states):
                draw_sample(frame, poses, sample); window_coverage.saved = True
            if all(s in (tf.SEEN, tf.FILLED) for s in states):
                both += 1
                upper += all(tf.upper_ok(poses[j, :, 2]) for j in range(2))
                rnc += bool(rnc_ok(poses))
                low += rnc_low(poses)
        i += 1
    cap.release()
    window_coverage.last_fallback_pct = 100 * fb / max(n, 1)
    window_coverage.last_low_pct = 100 * low / max(n, 1)
    return n, 100 * both / max(n, 1), 100 * upper / max(n, 1), 100 * rnc / max(n, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--score_thr", type=float, default=0.3)
    ap.add_argument("--nms_thr", type=float, default=0.65)
    ap.add_argument("--model", default="rtmo", help='"rtmo" (default) or a YOLO-pose .onnx, e.g. models/rncv_pose_v1.onnx')
    ap.add_argument("--out", default="reports/pose_attempts.md")
    ap.add_argument("--samples", default="", help="folder to save one landmark frame per attempt (skeletons drawn), local only")
    ap.add_argument("--fallback-rtmo", action="store_true", help="use RTMO-m on frames where --model keeps fewer than 2 fighters")
    args = ap.parse_args()
    labels = pd.read_csv(ROOT / "phase3_labels/labels.csv", dtype=str, keep_default_na=False)
    fallback = None
    if args.fallback_rtmo:   # combined: main model first, RTMO-m when it keeps < 2 fighters
        from rtmlib import RTMO
        fallback = (RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu"), 0.3)
    if args.model == "rtmo":
        from rtmlib import RTMO
        model = RTMO(onnx_model=RTMO_M, model_input_size=(640, 640), backend="onnxruntime", device="cpu")
        model_name = "RTMO-m"
    else:
        from yolo_pose_onnx import YoloPoseOnnx   # fine-tuned YOLO-pose (Kaggle), see docs/KAGGLE_FINETUNE.md
        model = YoloPoseOnnx(ROOT / args.model)
        model_name = Path(args.model).name + (" + RTMO-m fallback" if fallback else "")
    rows = []
    for k, r in labels.iterrows():
        clip = ROOT / "data/clips" / r.video_url
        if not r.video_url or not clip.exists():
            rows.append((k + 1, r.video_url or "—", r.outcome, "", "clip not found", "", "", "", "", ""))
            continue
        t0, t1 = float(r.video_time_start), float(r.video_time_end)
        n, both, upper, rnc = window_coverage(model, clip, t0, t1, args.stride, args.score_thr, args.nms_thr, fallback,
                                            (ROOT / args.samples / f"row{k + 1:02d}.jpg") if args.samples else None)
        flag = "🟢" if both >= GATE else "🔴"
        rows.append((k + 1, r.video_url, r.outcome, f"{t0:.1f}-{t1:.1f}", n, f"{flag} {both:.0f}%", f"{upper:.0f}%", f"{rnc:.0f}%", f"{window_coverage.last_low_pct:.0f}%", r.get("back_context", "") or "?"))
        print(f"row {k + 1}: both tracked {both:.0f}%, upper OK {upper:.0f}%, RNC-usable {rnc:.0f}%, fallback used {window_coverage.last_fallback_pct:.0f}% of frames", flush=True)
    ok = [float(x[5].split()[1][:-1]) for x in rows if isinstance(x[4], int)]
    lines = ["# Pose coverage inside labeled attempts", "",
             f"{model_name} (CPU), score {args.score_thr} / nms {args.nms_thr}, two-fighter selection with the referee filter, stride {args.stride}. "
             f"Gate (PLAN 2b): both fighters tracked in >= {GATE:.0f}% of frames.", "",
             "| Row | Clip | Outcome | Window (video s) | Frames | Both fighters tracked | Both upper bodies OK | RNC-usable | RNC-usable (low bar) | Context |", "|---|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {' | '.join(str(x) for x in r)} |" for r in rows]
    if ok:
        lines += ["", f"Median both-tracked across {len(ok)} attempts: **{np.median(ok):.0f}%**; "
                      f"{sum(x >= GATE for x in ok)}/{len(ok)} attempts pass the gate."]
        rq = [float(x[7][:-1]) for x in rows if isinstance(x[4], int)]
        lq = [float(x[8][:-1]) for x in rows if isinstance(x[4], int)]
        ctx = {}
        for x in rows:
            if isinstance(x[4], int):
                ctx.setdefault(x[9], []).append(float(x[8][:-1]))
        lines += [f"Median **RNC-usable (low bar)**: **{np.median(lq):.0f}%** (defender head + a shoulder; choker's wrist/elbow at the neck or knee/ankle at the waist, "
                  f"choker joints accepted at confidence >= {LOW}). By context: " + "; ".join(f"{k} {np.median(v):.0f}% (n={len(v)})" for k, v in sorted(ctx.items()))]
        lines += [f"Median **RNC-usable** frames: **{np.median(rq):.0f}%** (defender head + both shoulders, attacker head + one shoulder close to the defender's head; "
                  "the attacker's arms may be hidden, see `rnc_ok` in src/pose_attempts.py)."]
    lines += ["", "Re-run after the Kaggle fine-tune with the new model to compare (same command)."]
    (ROOT / args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
