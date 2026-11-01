"""Find labeled clips with no saved video or crops again, official sources only (local, data/clips/restored/).

    python -I tools/restore_search.py

There's no logged link, so each is searched by fighter names. A different upload could shift the labeled timestamps, so a
download is kept only if its frames match the saved detector features at the same seconds (median cosine >= MIN_MATCH).
Anything else is deleted and reported.
"""
import csv
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "data/clips/restored"
MIN_MATCH = 0.85
SAMPLES = 24


def match(path, npz, det, model, prep):
    import torch
    from PIL import Image

    import attempt_clf as ac
    d = np.load(npz)
    picks = np.linspace(0, len(d["t"]) - 1, SAMPLES).astype(int)
    cap = cv2.VideoCapture(str(path))
    sims = []
    for j in picks:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(d["t"][j]) * 1000)
        ok, f = cap.read()
        if not ok:
            sims.append(0.0)
            continue
        g = ac.pair_crop(det, f)
        with torch.no_grad():
            e = model.encode_image(prep(Image.fromarray(cv2.cvtColor(g, cv2.COLOR_BGR2RGB))).unsqueeze(0)).float()
        e = (e / e.norm(dim=-1, keepdim=True)).numpy()[0]
        sims.append(float(e @ d["X"][j]))
    cap.release()
    return float(np.median(sims))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import open_clip

    import attempt_clf as ac
    import fetch_clips as fc
    from yolo_pose_onnx import YoloPoseOnnx
    OUT.mkdir(parents=True, exist_ok=True)
    det = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    model, _, prep = open_clip.create_model_and_transforms(ac.ARCH, pretrained=ac.WEIGHTS)
    model.eval()
    rows = list(csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")))
    clips = {}
    for r in rows:
        clips.setdefault(r["video_url"], r)
    disk = {p.name for p in (ROOT / "data/clips").rglob("*")}
    kept = gone = 0
    for name, r in sorted(clips.items()):
        npz = ROOT / "data/attempt_clf/clips_crop" / f"{name}.npz"
        if name in disk or not npz.exists() or (ROOT / "data/crops" / name / "index.csv").exists():
            continue
        hit = fc.search(r["attacker"], r["defender"])
        if not hit:
            print(name, "no official video", flush=True); gone += 1
            continue
        tmp = OUT / f"_tmp_{hit[0]}"
        ok = subprocess.run(["yt-dlp", "-q", "--no-playlist", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                             "-o", f"{tmp}.%(ext)s", f"https://www.youtube.com/watch?v={hit[0]}"]).returncode == 0
        got = next(iter(OUT.glob(f"_tmp_{hit[0]}.mp4")), None)
        if not ok or got is None:
            print(name, "download failed", flush=True); gone += 1
            continue
        m = match(got, npz, det, model, prep)
        if m >= MIN_MATCH:
            got.rename(OUT / name); kept += 1
            print(name, f"KEPT match {m:.2f} {hit[1]} | {hit[3]}", flush=True)
        else:
            got.unlink(); gone += 1
            print(name, f"removed, timing doesn't match ({m:.2f}) {hit[1]} | {hit[3]}", flush=True)
    print(f"kept {kept}, not restored {gone}")


if __name__ == "__main__":
    main()
