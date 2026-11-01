"""Crude automatic demo: no hand labels on the fight being shown.

    python -I tools/mvp/auto_demo.py <clip> --round 2      # data/mvp/<clip>_auto.mp4: local only, it has broadcast pixels
    python -I tools/mvp/auto_demo.py --score               # reports/auto_demo.md: the same pipeline scored on every labeled fight

The detector (trained without this fight) finds the back attack. Public round stats pick the likely attacker (more control
in that round) and give the odds, from a small model trained on the other fights' outcomes. The finish time is the typical
window on the neck, not a prediction for this choke. Nothing reads the position, and the round number is given by hand
because nothing reads the on-screen clock yet.
"""
import csv
import math
import statistics as stx
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "research/model"), str(ROOT / "tools/mvp")]
import damage as dm  # noqa: E402
import detector_live as dl  # noqa: E402

W, H, PANEL = 1600, 900, 410
LEAD, TAIL, MAX_S = 8.0, 5.0, 120.0
INK, DIM, ORANGE, BG = (235, 238, 242), (140, 150, 162), (249, 115, 22), (13, 16, 22)
F = lambda s: ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", s)
SUCCESS = {"tap", "ref_stop", "unconscious"}


def labels():
    return [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8"))
            if "excluded_" not in r["notes"] and r["outcome"] != "bell"]


def control():
    """(fight_id, round) -> {fighter: control seconds} from the public stats."""
    fid = {}
    for r in csv.DictReader(open(dm.RAW / "ufc_fight_details.csv", encoding="utf-8")):
        fid[(r["EVENT"].strip(), " ".join(r["BOUT"].split()))] = r["URL"].strip().rsplit("/", 1)[-1]
    out = {}
    for r in csv.DictReader(open(dm.RAW / "ufc_fight_stats.csv", encoding="utf-8")):
        k = fid.get((r["EVENT"].strip(), " ".join(r["BOUT"].split())))
        if k and r["ROUND"].startswith("Round") and ":" in r["CTRL"]:
            m, s = r["CTRL"].split(":")
            out.setdefault((k, int(r["ROUND"].split()[1])), {})[r["FIGHTER"].strip()] = int(m) * 60 + int(s)
    return out


def likely_attacker(ctrl, fight, rnd):
    """(attacker, defender) by control time in the round, or None if the fight isn't in the stats."""
    c = ctrl.get((fight, rnd))
    if not c or len(c) < 2:
        return None
    a, b = sorted(c, key=c.get, reverse=True)[:2]
    return a, b


def features(stats, fight, rnd, att, dfn):
    d = dm.damage({"fight_id": fight, "round": str(rnd), "attacker": att, "defender": dfn}, stats)
    return [math.log1p(d[1]), d[0], rnd]


def train(rows, stats, leave_out):
    from sklearn.linear_model import LogisticRegression
    use = [r for r in rows if r["fight_id"] != leave_out]
    X = [features(stats, r["fight_id"], int(r["round"]), r["attacker"], r["defender"]) for r in use]
    y = [r["outcome"] in SUCCESS for r in use]
    clf = LogisticRegression(C=1.0, max_iter=3000).fit(np.array(X, float), y)
    secs = sorted(float(r["video_time_end"]) - float(r["video_time_start"]) for r in use if r["outcome"] in SUCCESS)
    return clf, secs[len(secs) // 4], stx.median(secs), secs[3 * len(secs) // 4]


def events(t, p):
    gate, out, cur = dl.Gate(t, p), [], None
    for now in t:
        on, _ = gate(float(now))
        if on and cur is None:
            cur = float(now)
        elif not on and cur is not None:
            out.append((cur, float(now))); cur = None
    if cur is not None:
        out.append((cur, float(t[-1])))
    return out


def score():
    rows, stats, ctrl = labels(), dm.stats_by_fight(), control()
    by = {}
    for r in rows:
        by.setdefault(r["video_url"], []).append(r)
    res, right, total, alarms, minutes, missed = [], 0, 0, 0, 0.0, 0
    for name, rs in sorted(by.items()):
        if not (ROOT / "data/attempt_clf/clips_crop" / f"{name}.npz").exists():
            continue
        fight = rs[0]["fight_id"]
        t, p = dl.scores(name, fight)
        ev = events(t, p)
        minutes += len(t) / 2 / 60
        clf, _, med, _ = train(rows, stats, fight)
        used = set()
        for r in rs:
            a, b = float(r["video_time_start"]), float(r["video_time_end"])
            hit = next((e for e in ev if e[0] <= b and e[1] >= a), None)
            if hit is None:
                missed += 1
                continue
            used.add(hit)
            pair = likely_attacker(ctrl, fight, int(r["round"]))
            if pair is None:
                continue
            total += 1
            right += dm.surname(pair[0]) == dm.surname(r["attacker"])
            x = np.array([features(stats, fight, int(r["round"]), *pair)], float)
            base = np.mean([q["outcome"] in SUCCESS for q in rows if q["fight_id"] != fight])
            res.append((float(clf.predict_proba(x)[0, 1]), r["outcome"] in SUCCESS, abs(hit[0] + med - b), abs(a + med - b), base))
        alarms += len(set(ev) - used)
    p = np.array([q[0] for q in res]); y = np.array([q[1] for q in res], float); base = np.array([q[4] for q in res])
    out = ["# Crude automatic pipeline, scored (exploratory)", "",
           "Generated by `tools/mvp/auto_demo.py --score`. On each fight: detector and odds trained without it, no position labels. "
           "The round number comes from labels, and only attempts the detector caught are scored. Finish-enriched sample.", "",
           "| Measure | Result | Compare with |", "|---|---|---|",
           f"| Attempts caught | {len(res) + missed - (total - len(res))} caught, {missed} missed | |",
           f"| False alarms | {alarms / max(minutes, 1e-9):.2f} per minute | |",
           f"| Likely attacker correct (more control in the round) | {right}/{total} ({100 * right / total:.0f}%) | |",
           f"| Finish odds, Brier | {np.mean((p - y) ** 2):.3f} | {np.mean((base - y) ** 2):.3f} for always guessing the other fights' average |",
           f"| End time from the detector's start, median error | {stx.median(q[2] for q in res):.1f} s | {stx.median(q[3] for q in res):.1f} s if the true start were known |"]
    (ROOT / "reports/auto_demo.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


def side(img, x0, det, names, pct, secs, q1, med, q3, stopped):
    d = ImageDraw.Draw(img)
    d.rectangle((x0, 0, W, H), fill=BG)
    x = x0 + 24
    d.text((x, 22), "RNCV // AUTOMATIC", font=F(20), fill=DIM)
    d.text((x, 48), "no hand labels on this fight", font=F(17), fill=DIM)
    d.rectangle((x, 84, W - 24, 128), fill=ORANGE if det else (32, 37, 45))
    d.text((x + 12, 95), "BACK ATTACK DETECTED" if det else "watching", font=F(22), fill=INK)
    if names:
        d.text((x, 150), f"{names[0].upper()} (likely attacker)", font=F(20), fill=INK)
        d.text((x, 180), f"{pct:.0f}%", font=F(92), fill=ORANGE)
        d.text((x, 284), "FINISH CHANCE, from public stats", font=F(19), fill=DIM)
        d.text((x, 310), "it can't see the choke itself", font=F(17), fill=DIM)
    if secs is not None:
        d.text((x, 370), f"{secs:.0f} s", font=F(60), fill=INK)
        d.text((x, 438), "SINCE THE BACK ATTACK WAS FLAGGED", font=F(19), fill=DIM)
        d.text((x, 474), "Time to a finish: not reliable yet", font=F(20), fill=INK)
        d.text((x, 502), "the flag starts before the choke does", font=F(18), fill=DIM)
    elif stopped:
        d.text((x, 370), "ended", font=F(44), fill=DIM)
    d.text((x, H - 40), "detector trained without this fight", font=F(15), fill=DIM)


def render(clip, rnd):
    rows, stats, ctrl = labels(), dm.stats_by_fight(), control()
    mine = [r for r in rows if r["video_url"] == clip.name]
    if not mine:
        raise SystemExit("the demo needs a fight whose id is known: pick a clip listed in labels.csv")
    fight = mine[0]["fight_id"]                     # identifies the fight only; no position or time from the labels is used
    t, p = dl.scores(clip.name, fight)
    ev = events(t, p)
    if not ev:
        raise SystemExit("the detector fired nowhere on this clip")
    clf, q1, med, q3 = train(rows, stats, fight)
    pair = likely_attacker(ctrl, fight, rnd)
    pct = 100 * clf.predict_proba(np.array([features(stats, fight, rnd, *pair)], float))[0, 1] if pair else 0.0
    lo = max(0.0, ev[0][0] - LEAD)
    hi = min(lo + MAX_S, ev[-1][1] + TAIL)
    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    vw, vh = int(cap.get(3)), int(cap.get(4))
    s = min((W - PANEL) / vw, H / vh); nw, nh = int(vw * s), int(vh * s)
    ox, oy = (W - PANEL - nw) // 2, (H - nh) // 2
    out = ROOT / "data/mvp" / f"{clip.stem}_auto.mp4"
    wr = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    cap.set(cv2.CAP_PROP_POS_MSEC, lo * 1000)
    while True:
        ok, fr = cap.read()
        now = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if not ok or now > hi:
            break
        canvas = np.zeros((H, W, 3), np.uint8); canvas[:] = BG[::-1]
        canvas[oy:oy + nh, ox:ox + nw] = cv2.resize(fr, (nw, nh))
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        cur = next((e for e in ev if e[0] <= now <= e[1]), None)
        past = any(e[1] < now for e in ev)
        side(img, W - PANEL, cur is not None, pair if cur or past else None, pct, now - cur[0] if cur else None, q1, med, q3, past and not cur)
        wr.write(cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR))
    cap.release(); wr.release()
    print("wrote", out, f"{len(ev)} detection(s), stretch {lo:.0f}-{hi:.0f} s, odds {pct:.0f}%, attacker {pair}")


if __name__ == "__main__":
    if "--score" in sys.argv:
        score()
    else:
        render(Path(sys.argv[1]), int(sys.argv[sys.argv.index("--round") + 1]))
