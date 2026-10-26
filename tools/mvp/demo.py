"""RNCV MVP 0.1: replay demo overlay for one labeled clip.

    python -I tools/mvp/demo.py data/clips/<clip>.mp4 [--out data/mvp/<clip>_demo.mp4]

What is real vs. stand-in (MVP 0.1):
- Attempt windows and the RNC factors come from YOUR LABELS (phase3_labels/labels.csv), not from automatic
  detection (the attempt detector is at ROC-AUC 0.70, not usable yet; see reports/attempt_clf_crop.md).
- The finish % is a small, honest demo model fit on the OTHER fights' labels (leave-one-fight-out, so the
  clip being shown never trains its own prediction): base finish rate x odds ratios for arm under chin,
  strong leg control and defender two-on-one, updated live from the G-panel state changes, and ramped up
  with time held (finishes take ~median success duration). It never peeks at the outcome.
- At the labeled end the result is shown (TAP / OUT / ESCAPE / ...) and the health bar settles; that's a
  replay marker, after the event, like a broadcast graphic.
Video stays local (data/ is git-ignored).
"""
import argparse
import csv
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SUCCESS = {"tap", "ref_stop", "unconscious"}
W, H, PANEL = 1600, 900, 420
BG, INK, DIM, LINE = (14, 17, 22), (231, 235, 240), (139, 149, 163), (44, 51, 61)
ATT, DEF, GOOD, BAD = (255, 138, 61), (76, 194, 255), (95, 211, 141), (255, 92, 92)
F = lambda n, s: ImageFont.truetype(f"C:/Windows/Fonts/{n}", s)
MONO, MONO_B, SANS_B = F("consola.ttf", 15), F("consolab.ttf", 15), F("bahnschrift.ttf", 22)
BIG = F("bahnschrift.ttf", 54)
OUTCOME_TXT = {"tap": "TAP", "ref_stop": "REF STOP", "unconscious": "OUT COLD", "escape": "ESCAPED",
               "position_change": "LET GO", "bell": "SAVED BY THE BELL"}


# ---------------- demo model ----------------
def strong_legs(v):
    return v in ("two_hooks", "body_triangle")


def fit(rows):
    """Base rate + smoothed odds ratios from the given attempts (bell = censored, skipped)."""
    rows = [r for r in rows if r["outcome"] != "bell"]
    y = np.array([r["outcome"] in SUCCESS for r in rows])
    def odds_ratio(mask_known, mask_yes):
        a = (y & mask_yes & mask_known).sum() + .5; b = (~y & mask_yes & mask_known).sum() + .5
        c = (y & ~mask_yes & mask_known).sum() + .5; d = (~y & ~mask_yes & mask_known).sum() + .5
        return float(np.clip((a / b) / (c / d), 0.25, 4.0))   # shrink: tiny data
    arm = np.array([r["choke_arm_position"] for r in rows]); ctl = np.array([r["control"] for r in rows])
    two = np.array([r["defender_two_on_one"] for r in rows])
    dur = [float(r["video_time_end"]) - float(r["video_time_start"]) for r, s in zip(rows, y) if s]
    return {"base": (y.sum() + 1) / (len(y) + 2), "n": len(y),
            "or_arm": odds_ratio(np.isin(arm, ["under_chin", "over_jaw"]), arm == "under_chin"),
            "or_legs": odds_ratio(ctl != "", np.array([strong_legs(v) for v in ctl])),
            "or_two": odds_ratio(np.isin(two, ["True", "False"]), two == "True"),
            "tau": float(np.median(dur)) if dur else 10.0}


def finish_prob(m, state):
    o = m["base"] / (1 - m["base"])
    if state.get("choke_arm_position") in ("under_chin", "over_jaw"):
        o *= m["or_arm"] if state["choke_arm_position"] == "under_chin" else 1 / m["or_arm"] ** .5
    if state.get("control"):
        o *= m["or_legs"] if strong_legs(state["control"]) else 1 / m["or_legs"] ** .5
    if state.get("defender_two_on_one") in ("True", "False"):
        o *= m["or_two"] if state["defender_two_on_one"] == "True" else 1
    return o / (1 + o)


def state_at(row, t_rel):
    """Landmark values, then G-panel changes logged up to t_rel seconds into the attempt."""
    st = {k: row.get(k, "") for k in ("choke_arm_position", "control", "defender_two_on_one", "rnc_style_at_L",
                                      "back_context", "chin_tucked", "upper_body")}
    st["rnc_style"] = st.pop("rnc_style_at_L")
    for ch in filter(None, row.get("state_changes", "").split(">")):
        try:
            t, kv = ch.split(":", 1); k, v = kv.split("=", 1)
        except ValueError:
            continue
        if float(t) <= t_rel:
            st[k] = v
    return st


# ---------------- drawing ----------------
def bar(d, x, y, w, h, frac, col, back=LINE):
    d.rounded_rectangle([x, y, x + w, y + h], 4, fill=back)
    if frac > 0:
        d.rounded_rectangle([x, y, x + max(6, int(w * frac)), y + h], 4, fill=col)


def panel(img, att, dfn, fin, hist, st, att_t, banner, model, live, air=None, grip=1.0, band=None):
    d = ImageDraw.Draw(img)
    x0 = W - PANEL
    d.rectangle([x0, 0, W, H], fill=BG); d.line([x0, 0, x0, H], fill=LINE, width=2)
    x = x0 + 24
    d.text((x, 18), "RNCV // RNC MONITOR", font=MONO_B, fill=DIM)
    d.text((x, 38), f"rear-naked choke · finish model {model['label']} (replay)", font=MONO, fill=DIM)
    # attacker: finish % grows
    d.text((x, 78), "ATTACKER", font=MONO, fill=ATT); d.text((x, 96), att[:22], font=SANS_B, fill=INK)
    d.text((x, 124), f"{round(100 * fin):d}%", font=BIG, fill=ATT if live else DIM)
    d.text((x + 150, 136), "finish chance", font=MONO, fill=DIM)
    if band and live:
        d.text((x + 150, 154), f"80% band {round(100 * band[0])}–{round(100 * band[1])}%", font=MONO, fill=DIM)
    bar(d, x, 192, PANEL - 48, 14, fin, ATT)
    d.text((x, 210), "grip", font=MONO, fill=DIM); bar(d, x + 50, 214, 120, 6, grip, (200, 120, 60))
    # defender: health drains
    hp = 1 - fin if air is None else air
    d.text((x, 228), "DEFENDER", font=MONO, fill=DEF); d.text((x, 246), dfn[:22], font=SANS_B, fill=INK)
    d.text((x, 278), "CHOKE METER (model)", font=MONO, fill=DIM); d.text((x + PANEL - 110, 278), f"{round(100 * hp):d}/100", font=MONO_B, fill=INK)
    hcol = GOOD if hp > .6 else (255, 200, 87) if hp > .3 else BAD
    bar(d, x, 300, PANEL - 48, 22, hp, hcol)
    # sparkline of finish % over the attempt
    sy, sh, sw = 350, 70, PANEL - 48
    d.rectangle([x, sy, x + sw, sy + sh], outline=LINE)
    for gy in (.25, .5, .75):
        d.line([x, sy + sh * (1 - gy), x + sw, sy + sh * (1 - gy)], fill=(28, 33, 41))
    if len(hist) > 1:
        pts = [(x + sw * i / max(1, len(hist) - 1), sy + sh * (1 - v)) for i, v in enumerate(hist)]
        d.line(pts, fill=ATT, width=2)
    d.text((x, sy + sh + 4), f"attempt {att_t:5.1f}s", font=MONO, fill=DIM)
    # state
    y = 460
    d.text((x, y), "STATE", font=MONO_B, fill=DIM); y += 24
    rows = [("arm", st.get("choke_arm_position") or "—", st.get("choke_arm_position") == "under_chin"),
            ("legs", st.get("control") or "—", strong_legs(st.get("control", ""))),
            ("upper body", st.get("upper_body") or "—", st.get("upper_body") == "body_lock"),
            ("grip", st.get("rnc_style") or "—", False),
            ("defender 2-on-1", {"True": "yes", "False": "no"}.get(st.get("defender_two_on_one", ""), "—"), False),
            ("chin tucked", {"True": "yes", "False": "no"}.get(st.get("chin_tucked", ""), "—"), st.get("chin_tucked") == "False"),
            ("position", st.get("back_context") or "—", False)]
    for k, v, hot in rows:
        d.text((x, y), k, font=MONO, fill=DIM)
        d.text((x + 170, y), v.replace("_", " "), font=MONO_B, fill=ATT if hot else INK); y += 22
    # model footer
    d.line([x, H - 92, W - 24, H - 92], fill=LINE)
    d.text((x, H - 84), f"priors: you + research{' + coach' if model['label'] == 'v0.7c' else ''} + {model['n']} labels", font=MONO, fill=DIM)
    d.text((x, H - 64), "other fights only (leave-one-fight-out)", font=MONO, fill=DIM)
    d.text((x, H - 44), "replay: windows + factors from labels", font=MONO, fill=DIM)
    if banner:
        txt, col = banner
        bw = d.textlength(txt, font=BIG)
        cx = (W - PANEL) // 2
        d.rounded_rectangle([cx - bw / 2 - 24, 40, cx + bw / 2 + 24, 120], 10, fill=(0, 0, 0))
        d.text((cx - bw / 2, 48), txt, font=BIG, fill=col)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--out", default="")
    ap.add_argument("--no-track", action="store_true", help="skip the fighter tracking layer")
    ap.add_argument("--model", choices=["v06", "v07c"], default="v07c",
                    help="v07c = current model (v0.7 structure: grip type, body triangle; + coach priors); v06 = previous")
    ap.add_argument("--panel-only", action="store_true",
                    help="footage-free output: only the readout panel around the attempts (+ a GIF), shareable")
    a = ap.parse_args()
    clip = Path(a.clip)
    rows = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
    rows = [r for r in rows if "excluded_" not in r["notes"]]
    mine = sorted([r for r in rows if r["video_url"] == clip.name], key=lambda r: float(r["video_time_start"]))
    if not mine:
        raise SystemExit(f"no labeled attempts for {clip.name}")
    import sys
    sys.path.insert(0, str(ROOT / "research/model"))
    import state_model as sm                     # finish model v0.6 (docs/MODEL_SPEC.md)
    train = [r for r in sm.load() if r["fight_id"] != mine[0]["fight_id"]]
    if a.model == "v07c":                        # v0.7 + coach priors (research/model/run_v07_coach.py)
        import model_v07 as m7
        import run_v07_coach as rc
        rc.setup(); sm.USE_FATIGUE = False
        m7.D0.update(m7.round_d0(sm.load()))
        sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
        cards = list(csv.DictReader(open(ROOT / "research/model/priors_v07.csv", encoding="utf-8")))
        beta, cov = rc.fit_cov(train, cards)
        x_at, fat_i, label = m7.x_at, m7.FEATS.index("fatigue"), "v0.7c"
    else:
        sm.USE_FATIGUE = True
        cards = list(csv.DictReader(open(ROOT / "research/model/priors_v06.csv", encoding="utf-8")))
        beta, cov = sm.fit_cov(train, cards)
        x_at, fat_i, label = sm.x_at, 7, "v0.6"
    model = {"cards": len(cards), "n": len(train), "label": label}
    airs = {id(r): [(tt, c) for tt, c, *_ in sm.consciousness_trace(r)] for r in mine}
    out = Path(a.out) if a.out else ROOT / "data/mvp" / f"{clip.stem}_demo.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(clip))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    vw, vh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    s = min((W - PANEL) / vw, H / vh); nw, nh = int(vw * s), int(vh * s)
    ox, oy = (W - PANEL - nw) // 2, (H - nh) // 2
    po = a.panel_only
    if po:                                       # no UFC pixels: panel only, attempts +- a few seconds
        out = out.with_name(out.stem.replace("_demo", "") + "_panel.mp4")
        t_lo = float(mine[0]["video_time_start"]) - 2.0
        t_hi = float(mine[-1]["video_time_end"]) + 4.0
        gif = []
    wr = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps, (PANEL, H) if po else (W, H))
    layer = None
    if not a.no_track and not po:
        sys.path.insert(0, str(ROOT / "tools/mvp"))
        import tracking
        layer = tracking.Layer(*tracking.compute(clip))
    hist, shown, last_end, i = [], 0.0, None, 0
    air, grip, band = 1.0, 1.0, None
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = i / fps; i += 1
        cur = next((r for r in mine if float(r["video_time_start"]) <= t <= float(r["video_time_end"])), None)
        canvas = np.zeros((H, W, 3), np.uint8); canvas[:] = BG[::-1]
        banner = None
        if cur:
            el = t - float(cur["video_time_start"])
            st = state_at(cur, el)
            xv = x_at(cur, el)
            target = sm.predict(beta, xv, sample=False)          # P(finish | state now), no time ramp
            band = sm.interval(beta, cov, xv)
            shown += (target - shown) * 0.35                      # light display smoothing only
            tr = airs[id(cur)]
            air = tr[min(len(tr) - 1, int(el / 0.1))][1] / 100
            grip = 1 - float(xv[fat_i])
            hist.append(shown); att_t = el; last_end = cur
            att, dfn, live = cur["attacker"], cur["defender"], True
        else:
            st = state_at(last_end, 1e9) if last_end else {}
            att = last_end["attacker"] if last_end else mine[0]["attacker"]
            dfn = last_end["defender"] if last_end else mine[0]["defender"]
            att_t, live = 0.0, False
            if last_end and t - float(last_end["video_time_end"]) < 3:
                o = last_end["outcome"]
                banner = (OUTCOME_TXT.get(o, o.upper()), BAD if o in SUCCESS else DEF)
                shown += ((1.0 if o in SUCCESS else 0.0) - shown) * 0.5
                if o in SUCCESS:
                    air = max(0.0, air - 0.1)
            else:
                shown *= 0.9; hist = [] if shown < .01 else hist
                air = min(1.0, air + 0.02); grip = min(1.0, grip + 0.02)
        if layer is not None:                             # tracking + readouts drawn on the fighters
            fr = layer.draw(fr, i - 1, t, live, fin=shown, air=air, banner=banner[0] if banner else None)
        canvas[oy:oy + nh, ox:ox + nw] = cv2.resize(fr, (nw, nh))
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        panel(img, att, dfn, shown, hist[-240:], st, att_t, banner, model, live, air, grip, band)
        if po:
            if t_lo <= t <= t_hi:
                pim = img.crop((W - PANEL, 0, W, H - 100))
                wr.write(cv2.cvtColor(np.asarray(img.crop((W - PANEL, 0, W, H))), cv2.COLOR_RGB2BGR))
                if i % 3 == 0:
                    gif.append(pim.resize((PANEL // 2 * 2 * 3 // 4, (H - 100) * 3 // 4)))
            continue
        wr.write(cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR))
    cap.release(); wr.release()
    if po and gif:
        g = out.with_suffix(".gif")
        gif[0].save(g, save_all=True, append_images=gif[1:], duration=int(3000 / fps), loop=0, optimize=True)
        print("wrote", g)
    print("wrote", out)


if __name__ == "__main__":
    main()
