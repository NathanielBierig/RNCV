"""Side tab for the replay demo (MVP 0.3, owner feedback 2026-10-27): numbers live in their own tab, not on the video.

Top: detector status (the real model: BACK ATTACK DETECTED / SCANNING) and the attacker's FINISH chance.
Middle: the defender's HP (modeled choke dose) and an estimate of the seconds of air left.
Bottom half: big factor boxes that land with a "boom" when the position changes. Colour = how much the current
model says the factor matters: gold = very helpful (x3+), purple = helpful (x1.5+), blue = small, red = against.
At the stoppage the finish section becomes the result (TAP / OUT COLD / ESCAPED).
"""
from PIL import ImageDraw, ImageFont

F = lambda n, s: ImageFont.truetype(f"C:/Windows/Fonts/{n}", s)
BIGNUM, MID, NAME, BOX, SMALL, TINY, RESULT = (F("bahnschrift.ttf", 78), F("bahnschrift.ttf", 30), F("bahnschrift.ttf", 22),
                                               F("bahnschrift.ttf", 24), F("bahnschrift.ttf", 16), F("bahnschrift.ttf", 13),
                                               F("bahnschrift.ttf", 64))
BG, INK, DIM, LINE = (14, 17, 22), (236, 239, 244), (139, 149, 163), (44, 51, 61)
AMBER, RED, BLUE = (255, 170, 40), (255, 70, 60), (76, 194, 255)
GOLD, PURPLE, CHIPBLUE, CHIPRED = (255, 196, 40), (178, 102, 255), (76, 160, 255), (255, 70, 60)
POP, BOOM = 1.2, 0.5            # seconds a new box stays lit / its shock ring lasts


def mix(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(x + (y - x) * f) for x, y in zip(a, b))


def tier(m):
    return GOLD if m >= 3.0 else PURPLE if m >= 1.5 else CHIPBLUE if m >= 0.8 else CHIPRED


def chips_for(st, mult):
    """(text, colour) for the visible factors, coloured by the current model's odds multipliers."""
    g = lambda k, d=1.0: mult.get(k, d)
    out = []
    arm = st.get("choke_arm_position")
    if arm == "under_chin":
        out.append(("ARM UNDER THE CHIN", tier(g("arm_under", 4.0))))
    elif arm == "over_jaw":
        out.append(("OVER THE JAW", tier(1 / g("arm_under", 4.0))))
    lock = st.get("rnc_style", "")
    if lock == "figure_four":
        out.append(("FIGURE-FOUR LOCK", tier(g("grip_f4", 2.4))))
    elif lock in ("palm_to_palm", "gable", "wrist_pull"):
        out.append((lock.replace("_", " ").upper() + " LOCK", tier(g("grip_other", 2.0))))
    c = st.get("control", "")
    if c == "body_triangle":
        out.append(("BODY TRIANGLE", tier(g("legs_bt", 1.1))))
    elif c == "two_hooks":
        out.append(("BOTH HOOKS IN", tier(g("legs_hooks", 1.0))))
    if st.get("opponent_flattened") == "True":
        out.append(("FLATTENED OUT", tier(g("flattened", 3.0))))
    if st.get("choking_hand_tucked") == "True":
        out.append(("CHOKING HAND HIDDEN", tier(g("hand_tucked", 1.6))))
    if st.get("defender_two_on_one") == "True":
        out.append(("2-ON-1 HAND FIGHT", tier(g("two_on_one", 0.5))))
    if st.get("chin_tucked") == "True":
        out.append(("CHIN TUCKED", tier(g("chin_tucked", 0.85))))
    return out


class Panel:
    def __init__(self, x0, W, H, mult=None, label="v0.7c"):
        self.x0, self.W, self.H, self.mult, self.label = x0, W, H, mult or {}, label
        self.seen = {}

    def bar(self, d, x, y, w, h, frac, col):
        d.rounded_rectangle([x, y, x + w, y + h], 5, fill=LINE)
        if frac > 0.005:
            d.rounded_rectangle([x, y, x + max(8, int(w * frac)), y + h], 5, fill=col)

    def draw(self, img, t, att, dfn, fin, hp, secs, st, live, det=None, end=None):
        d = ImageDraw.Draw(img, "RGBA")
        x0, W, H = self.x0, self.W, self.H
        x, w = x0 + 24, W - x0 - 48
        d.rectangle([x0, 0, W, H], fill=BG)
        d.line([x0, 0, x0, H], fill=LINE, width=2)
        d.text((x, 16), "RNCV // RNC MONITOR", font=SMALL, fill=DIM)
        d.text((x, 36), f"finish model {self.label} · replay", font=TINY, fill=DIM)
        # detector strip (the real computer-vision model, trained without this fight)
        if det is not None:
            on, p = det
            if on:
                pulse = 0.7 + 0.3 * abs(((t * 1.6) % 2) - 1)
                d.rounded_rectangle([x, 60, x + w, 96], 7, fill=mix(AMBER, RED, 0.6) + (int(255 * pulse),))
                d.text((x + 12, 66), "BACK ATTACK DETECTED", font=NAME, fill=BG)
            else:
                d.rounded_rectangle([x, 60, x + w, 96], 7, outline=LINE, width=2)
                d.text((x + 12, 66), "SCANNING", font=NAME, fill=DIM)
                self.bar(d, x + 140, 74, w - 156, 8, min(1.0, p), AMBER)
        # finish chance (attacker) or the result
        y = 116
        if end:
            res, held, peak, finished = end
            col = RED if finished else BLUE
            d.text((x, y), res, font=RESULT, fill=col)
            d.text((x, y + 76), f"{held:.1f} s on the neck", font=NAME, fill=INK)
            d.text((x, y + 104), f"model read {round(100 * peak)}% at its peak", font=SMALL, fill=DIM)
        else:
            d.text((x, y), (att.upper() if live else "—"), font=NAME, fill=INK)
            fcol = mix(AMBER, RED, (fin - 0.5) / 0.5) if live else DIM
            num = f"{round(100 * fin)}%" if live else "—"
            d.text((x, y + 22), num, font=BIGNUM, fill=fcol)
            d.text((x + d.textlength(num, font=BIGNUM) + 14, y + 66), "FINISH CHANCE", font=SMALL, fill=DIM)
            self.bar(d, x, y + 112, w, 12, fin if live else 0, fcol)
        # defender HP + seconds of air left (estimate)
        y = 270
        hcol = mix(RED, BLUE, (hp - 0.2) / 0.6)
        d.text((x, y), f"{dfn.split()[-1].upper()}  HP", font=NAME, fill=INK)
        d.text((x + w - d.textlength(f"{round(100 * hp)}", font=MID), y - 6), f"{round(100 * hp)}", font=MID, fill=hcol)
        self.bar(d, x, y + 32, w, 18, hp, hcol)
        air = "breathing" if secs is None else ("out" if secs <= 0.2 else f"≈ {secs:.0f} s of air left" if secs < 20 else "> 20 s of air left")
        d.text((x, y + 58), air + ("" if secs is None else "  (estimate)"), font=SMALL, fill=hcol if secs is not None else DIM)
        # factor boxes (bottom half)
        y = 372
        d.line([x, y, x + w, y], fill=LINE)
        d.text((x, y + 10), "WHAT DECIDES IT", font=SMALL, fill=DIM)
        y += 40
        chips = chips_for(st, self.mult) if (live or end) else []
        for text, col in chips:
            self.seen.setdefault(text, t)
            age = t - self.seen[text]
            hot = age < POP
            bh = 58
            dx = int(60 * max(0.0, 0.2 - age) / 0.2)                                        # slides in fast
            if age < BOOM:                                                                  # the "boom": a shock ring
                g = int(4 + 22 * age / BOOM)
                d.rounded_rectangle([x + dx - g, y - g, x + w + g, y + bh + g], 12,
                                    outline=col + (int(255 * (1 - age / BOOM)),), width=4)
            d.rounded_rectangle([x + dx, y, x + w, y + bh], 9, fill=(col + (255,)) if hot else (BG + (255,)),
                                outline=col, width=3)
            d.rectangle([x + dx, y, x + dx + 12, y + bh], fill=col)
            d.text((x + dx + 28, y + 15), text, font=BOX, fill=BG if hot else INK)
            y += bh + 12
        for k in [k for k in self.seen if k not in {c for c, _ in chips}]:
            del self.seen[k]
        d.text((x, H - 30), "factors from labels · detector held out on this fight", font=TINY, fill=DIM)
