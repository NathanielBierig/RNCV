"""On-video HUD for the replay demo (MVP 0.3), after the owner's and the fresh-eyes review (2026-10-27).

One home per number: a lower-third card holds the attacker's FINISH chance and the defender's HP bar.
Big factor boxes on the left explain WHY and pop when the position changes. Their colour comes from the
model's own weights: gold = very helpful (x3+), purple = helpful (x1.5+), blue = small, red = against the finish.
One ending card at the stoppage. No green: the finish chance ramps amber to red, HP drains blue to red.
Drawn with PIL on the full-frame video (no side panel).
"""
from PIL import ImageDraw, ImageFont

F = lambda n, s: ImageFont.truetype(f"C:/Windows/Fonts/{n}", s)
NUM, LABEL, NAME, CHIP, END, ENDSUB, TAG = (F("bahnschrift.ttf", 64), F("bahnschrift.ttf", 16), F("bahnschrift.ttf", 22),
                                           F("bahnschrift.ttf", 26), F("bahnschrift.ttf", 84), F("bahnschrift.ttf", 24),
                                           F("bahnschrift.ttf", 14))
INK, DIM, CARD = (236, 239, 244), (150, 158, 170), (14, 17, 22)
AMBER, RED, BLUE = (255, 170, 40), (255, 70, 60), (76, 194, 255)
POP = 1.2                       # seconds a new chip stays highlighted


def mix(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(x + (y - x) * f) for x, y in zip(a, b))


GOLD, PURPLE, CHIPBLUE, CHIPRED = (255, 196, 40), (178, 102, 255), (76, 160, 255), (255, 70, 60)


def tier(m):
    """Chip colour from the model's own odds multiplier: gold = very helpful, purple = helpful,
    blue = small either way, red = works against the finish."""
    if m >= 3.0:
        return GOLD
    if m >= 1.5:
        return PURPLE
    if m >= 0.8:
        return CHIPBLUE
    return CHIPRED


def chips_for(st, mult):
    """(text, colour) for the visible factors, coloured by how much the current model says each one matters."""
    g = lambda k, d=1.0: mult.get(k, d)
    out = []
    arm = st.get("choke_arm_position")
    if arm == "under_chin":
        out.append(("UNDER THE CHIN", tier(g("arm_under", 4.0))))
    elif arm == "over_jaw":
        out.append(("OVER THE JAW", tier(1 / g("arm_under", 4.0))))
    lock = st.get("rnc_style", "")
    if lock == "figure_four":
        out.append(("FIGURE-FOUR", tier(g("grip_f4", 2.4))))
    elif lock in ("palm_to_palm", "gable", "wrist_pull"):
        out.append((lock.replace("_", " ").upper(), tier(g("grip_other", 2.0))))
    c = st.get("control", "")
    if c == "body_triangle":
        out.append(("BODY TRIANGLE", tier(g("legs_bt", 1.1))))
    elif c == "two_hooks":
        out.append(("BOTH HOOKS", tier(g("legs_hooks", 1.0))))
    if st.get("opponent_flattened") == "True":
        out.append(("FLATTENED OUT", tier(g("flattened", 3.0))))
    if st.get("choking_hand_tucked") == "True":
        out.append(("HAND HIDDEN", tier(g("hand_tucked", 1.6))))
    if st.get("defender_two_on_one") == "True":
        out.append(("2-ON-1 DEFENSE", tier(g("two_on_one", 0.5))))
    if st.get("chin_tucked") == "True":
        out.append(("CHIN TUCKED", tier(g("chin_tucked", 0.85))))
    return out


class Hud:
    def __init__(self, mult=None):
        self.seen = {}                  # chip text -> time it appeared (for the pop)
        self.mult = mult or {}

    def reset(self):
        self.seen = {}

    def detector(self, d, W, t, det):
        """Top-right: the real detector (held out on this fight). On = BACK ATTACK DETECTED, else SCANNING."""
        on, p = det
        x1, y0, w = W - 24, 18, 330
        x0 = x1 - w
        if on:
            pulse = 0.75 + 0.25 * abs(((t * 1.6) % 2) - 1)
            col = mix(AMBER, RED, 0.6)
            d.rounded_rectangle([x0, y0, x1, y0 + 58], 8, fill=(col + (int(235 * pulse),)))
            d.text((x0 + 16, y0 + 8), "BACK ATTACK DETECTED", font=CHIP, fill=CARD)
            d.text((x0 + 16, y0 + 36), f"detector {p:.2f}  ·  computer vision, no labels", font=TAG, fill=CARD)
        else:
            d.rounded_rectangle([x0, y0, x1, y0 + 58], 8, fill=CARD + (190,))
            d.text((x0 + 16, y0 + 8), "SCANNING", font=CHIP, fill=DIM)
            d.rounded_rectangle([x0 + 16, y0 + 40, x1 - 16, y0 + 48], 3, fill=(60, 64, 72, 255))
            d.rounded_rectangle([x0 + 16, y0 + 40, x0 + 16 + int((w - 32) * min(1.0, p)), y0 + 48], 3, fill=AMBER + (220,))

    def draw(self, img, t, att, dfn, fin, hp, st, live, fade=1.0, end=None, det=None):
        """img: PIL RGB frame. end = (result text, seconds held, peak finish, finished?) during the ending card."""
        W, H = img.size
        d = ImageDraw.Draw(img, "RGBA")
        a = int(255 * fade)
        d.text((24, 18), "RNCV  ·  RNC FINISH MODEL  ·  REPLAY", font=TAG, fill=DIM + (200,))
        if det is not None and not end:
            self.detector(d, W, t, det)
        if end:
            d.rectangle([0, 0, W, H], fill=(0, 0, 0, 110))                                  # dim the video
            res, held, peak, finished = end
            d.rectangle([0, int(H * 0.33), W, int(H * 0.33) + 150], fill=(10, 12, 16, 200))        # result band
            tw = d.textlength(res, font=END)
            d.text(((W - tw) / 2, H * 0.36), res, font=END, fill=RED if finished else BLUE)
            sub = f"{held:.1f} s on the neck  ·  model read {round(100 * peak)}% at its peak"
            sw = d.textlength(sub, font=ENDSUB)
            d.text(((W - sw) / 2, H * 0.36 + 100), sub, font=ENDSUB, fill=INK)
            return
        if not live:
            self.reset()
            return
        # factor boxes (left): big, coloured by strength, the newest one pops
        chips = chips_for(st, self.mult)
        y = int(H * 0.17)
        for text, col in chips:
            self.seen.setdefault(text, t)
            age = t - self.seen[text]
            hot = age < POP
            w, h = 300, 54
            x = 24 - int(40 * max(0.0, 0.25 - age) / 0.25)                                # slide in
            d.rounded_rectangle([x, y, x + w, y + h], 8, fill=(col + (235,)) if hot else (CARD + (215,)),
                                outline=col + (a,), width=3)
            d.rectangle([x, y, x + 10, y + h], fill=col + (a,))
            d.text((x + 24, y + 13), text, font=CHIP, fill=(CARD if hot else INK) + (a,))
            y += h + 10
        for k in [k for k in self.seen if k not in {c for c, _ in chips}]:
            del self.seen[k]                                                                # gone: may pop again
        # lower third (bottom-left, above the broadcast scorebug)
        cw, ch = 420, 132
        x0, y0 = 24, int(H * 0.80) - ch
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], 10, fill=CARD + (int(215 * fade),))
        fcol = mix(AMBER, RED, (fin - 0.5) / 0.5)
        d.rectangle([x0, y0, x0 + 6, y0 + ch], fill=fcol + (a,))
        d.text((x0 + 22, y0 + 10), att.upper(), font=NAME, fill=INK + (a,))
        d.text((x0 + 22, y0 + 34), f"{round(100 * fin)}%", font=NUM, fill=fcol + (a,))
        d.text((x0 + 22 + d.textlength(f"{round(100 * fin)}%", font=NUM) + 12, y0 + 64), "FINISH CHANCE", font=LABEL, fill=DIM + (a,))
        hcol = mix(RED, BLUE, (hp - 0.2) / 0.6)
        d.text((x0 + 22, y0 + 104), f"{dfn.split()[-1].upper()}  HP", font=LABEL, fill=INK + (a,))
        bx0, bx1 = x0 + 130, x0 + cw - 70
        d.rounded_rectangle([bx0, y0 + 106, bx1, y0 + 120], 4, fill=(60, 64, 72, a))
        if hp > 0.005:
            d.rounded_rectangle([bx0, y0 + 106, bx0 + max(6, int((bx1 - bx0) * hp)), y0 + 120], 4, fill=hcol + (a,))
        d.text((bx1 + 10, y0 + 102), f"{round(100 * hp)}", font=LABEL, fill=hcol + (a,))
