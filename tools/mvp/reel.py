"""30-second portfolio reel with no broadcast footage: docs/media/rncv_reel.mp4

    python tools/mvp/demo.py data/clips/demos/oliveira_gamrot.mp4.webm --no-pixels
    python tools/mvp/reel.py

    python tools/mvp/demo.py data/clips/demos/oliveira_gamrot.mp4.webm --out data/mvp/oliveira_gamrot.mp4_demo.mp4
    python tools/mvp/reel.py --footage      # data/mvp/rncv_reel_footage.mp4: real broadcast pixels, stays local (git-ignored)

Title card -> the derived-data replay at 1.5x with captions -> pilot rates with their 95% intervals -> end card.
The rates are read from reports/findings_pilot.md, so rerunning after new labels keeps the numbers current.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FOOTAGE = "--footage" in sys.argv
SRC = ROOT / f"data/mvp/oliveira_gamrot.mp4_{'demo' if FOOTAGE else 'nopixels'}.mp4"
OUT = ROOT / ("data/mvp/rncv_reel_footage.mp4" if FOOTAGE else "docs/media/rncv_reel.mp4")
FFMPEG = shutil.which("ffmpeg")
W, H, FPS = 1280, 720, 30
SPEED = 1.5
T_IN, T_OUT = 6.0, 34.5                     # stretch of the replay, in its own seconds
TITLE_S, RATES_S, END_S, FADE = 3.0, 5.5, 2.5, 0.3
CAPTIONS = [(6.0, 12.0, "A detector that never saw this fight flags the back attack"),
            (12.0, 19.5, "Position details are hand-labeled; the model turns them into a finish chance"),
            (19.5, 27.0, "The grip becomes a figure-four: the finish chance jumps"),
            (27.0, 34.5, "HP, the estimated air left, has run out. Then the tap")]
BG, INK, DIM, ORANGE, BLUE, GOLD = (13, 16, 22), (235, 238, 242), (140, 150, 162), (249, 115, 22), (74, 158, 255), (250, 190, 40)
F = lambda s: ImageFont.truetype("C:/Windows/Fonts/bahnschrift.ttf", s)


def rate(section, label):
    """(attempts, percent, low, high) of one row of the findings report."""
    text = (ROOT / "reports/findings_pilot.md").read_text(encoding="utf-8")
    block = text.split(f"## {section}")[1].split("\n## ")[0]
    m = re.search(rf"\| {re.escape(label)} \| (\d+) \| \d+ \((\d+)%\) \| (\d+)–(\d+)% \|", block)
    return tuple(int(v) for v in m.groups())


ROWS = [("Arm position", "under the chin", "Arm position (at 2 s)", "under the chin", "over the jaw", "over the jaw"),
        ("Grip", "figure-four", "Grip (at 2 s)", "figure-four", "one arm", "one arm / short choke"),
        ("Choking hand", "hidden", "Choking hand hidden (at 2 s)", "yes", "not hidden", "no"),
        ("Leg control", "one hook / none", "Legs (at 2 s)", "one hook / none", "body triangle", "body triangle")]


def card(lines):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    for text, y, size, color in lines:
        d.text((W / 2, y), text, font=F(size), fill=color, anchor="mm")
    return np.array(img)[:, :, ::-1].copy()


def rates_frame(grow):
    """Bars grow to the rate; the thin line is the 95% interval, so overlap is visible."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((70, 62), "First findings: how often the choke finished", font=F(38), fill=INK, anchor="lm")
    d.text((70, 108), "75 hand-labeled attempts from 43 UFC fights  ·  pre-registered study  ·  pilot", font=F(21), fill=DIM, anchor="lm")
    x0, full, y = 450, 720, 158
    for name, a_lab, sec, a_key, b_lab, b_key in ROWS:
        d.text((70, y + 32), name, font=F(27), fill=INK, anchor="lm")
        for j, (lab, key, col) in enumerate(((a_lab, a_key, ORANGE), (b_lab, b_key, BLUE))):
            n, pct, lo, hi = rate(sec, key)
            yy = y + 16 + j * 34
            d.text((x0 - 14, yy), lab, font=F(19), fill=DIM, anchor="rm")
            d.rectangle((x0, yy - 11, x0 + full * pct / 100 * grow, yy + 11), fill=col)
            if grow == 1:
                d.line((x0 + full * lo / 100, yy, x0 + full * hi / 100, yy), fill=INK, width=2)
                for v in (lo, hi):
                    d.line((x0 + full * v / 100, yy - 6, x0 + full * v / 100, yy + 6), fill=INK, width=2)
                d.text((x0 + full + 12, yy), f"{pct}%", font=F(22), fill=INK, anchor="lm")
        y += 100
    d.text((70, 618), "Directions, not proof.", font=F(29), fill=GOLD, anchor="lm")
    d.text((70, 658), "White lines are 95% ranges and they overlap. The confirmatory test runs at 150 attempts.", font=F(23), fill=INK, anchor="lm")
    return np.array(img)[:, :, ::-1].copy()


def caption(frame, text):
    """Band across the bottom of the replay pane; the side panel stays clear."""
    pane = int(W * 1180 / 1600)
    img = Image.fromarray(frame[:, :, ::-1])
    d = ImageDraw.Draw(img, "RGBA")
    font, size = F(25), 25
    while font.getlength(text) > pane - 50:
        size -= 1
        font = F(size)
    d.rectangle((0, H - 96, pane - 2, H - 50), fill=(13, 16, 22, 215))
    d.text((pane / 2, H - 73), text, font=font, fill=INK, anchor="mm")
    return np.array(img)[:, :, ::-1].copy()


def faded(frame, i, n):
    k = min(1.0, (i + 1) / (FADE * FPS), (n - i) / (FADE * FPS))
    return (frame.astype(np.float32) * k + np.array(BG[::-1], np.float32) * (1 - k)).astype(np.uint8)


def main():
    title = card([("Commentators say a choke is “in deep”.", H / 2 - 44, 50, INK),
                  ("This project measures it.", H / 2 + 28, 50, ORANGE),
                  ("Rear-naked chokes in the UFC" + ("" if FOOTAGE else "  ·  shown here as derived data, no broadcast footage"), H - 90, 22, DIM)])
    end = card([("RNCV", H / 2 - 64, 76, ORANGE),
                ("A pre-registered study and a replay finish-chance overlay", H / 2 + 8, 32, INK),
                ("Pilot: proof of concept, built from hand labels and computer vision", H / 2 + 56, 24, DIM)])
    enc = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)],
                           stdin=subprocess.PIPE)
    n = int(TITLE_S * FPS)
    for i in range(n):
        enc.stdin.write(faded(title, i, n).tobytes())

    cap = cv2.VideoCapture(str(SRC))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    n, last = int((T_OUT - T_IN) / SPEED * FPS), int(T_IN * src_fps) - 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, last + 1)
    frame = None
    for i in range(n):
        t = T_IN + i * SPEED / FPS
        want = int(t * src_fps)
        while last < want:
            ok, f = cap.read()
            assert ok, f"replay ended at {t:.1f} s"
            last += 1
            frame = f
        out = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
        text = next((c for a, b, c in CAPTIONS if a <= t < b), None)
        enc.stdin.write(faded(caption(out, text) if text else out, i, n).tobytes())

    n = int(RATES_S * FPS)
    done = rates_frame(1)
    for i in range(n):
        g = min(1.0, i / (0.9 * FPS))
        enc.stdin.write(faded(done if g == 1 else rates_frame(1 - (1 - g) ** 3), i, n).tobytes())
    n = int(END_S * FPS)
    for i in range(n):
        enc.stdin.write(faded(end, i, n).tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
