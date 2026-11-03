"""Recover labeled clips whose new download is the same fight on a different timeline (local, data/clips/restored/).

    python -I tools/restore_shift.py

For each labeled clip with no video and no crops: search an official upload (tools/fetch_clips.search), take image
fingerprints at 1 fps across it, and slide them against the saved fingerprints to find the time shift. If the best shift
matches well (median cosine >= MIN_MATCH), the video is trimmed or padded by that shift with ffmpeg so the labeled
seconds line up again, checked once more, and kept under the original name. Anything else is deleted.
"""
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "research/attempt_clf"), str(ROOT / "src"), str(ROOT / "tools")]
OUT = ROOT / "data/clips/restored"
MIN_MATCH, MAX_MIN = 0.85, 70


def fingerprints(path, det, model, prep, step=1.0):
    import torch
    from PIL import Image

    import attempt_clf as ac
    cap = cv2.VideoCapture(str(path))
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    ts, X, batch = [], [], []
    t = 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok:
            batch.append(prep(Image.fromarray(cv2.cvtColor(ac.pair_crop(det, f), cv2.COLOR_BGR2RGB)))); ts.append(t)
        if len(batch) == 32 or (t + step >= dur and batch):
            with torch.no_grad():
                e = model.encode_image(torch.stack(batch)).float()
            X.append((e / e.norm(dim=-1, keepdim=True)).numpy()); batch = []
        t += step
    return np.array(ts), np.concatenate(X)


def best_shift(saved, ts, X):
    """Shift d (seconds) so that the new video at saved_t + d matches the saved fingerprints at saved_t."""
    st, sX = saved["t"], saved["X"]
    keep = np.arange(0, len(st), 2)                          # 1 fps of the saved 2 fps
    best = (-1.0, 0.0)
    for d in np.arange(ts[0] - st[keep][-1], ts[-1] - st[keep][0], 1.0):
        j = np.rint(st[keep] + d - ts[0]).astype(int)
        ok = (j >= 0) & (j < len(ts))
        if ok.sum() < 0.6 * len(keep):
            continue
        m = float(np.median(np.sum(sX[keep][ok] * X[j[ok]], 1)))
        best = max(best, (m, float(d)))
    return best


def shift_video(src, dst, d, ffmpeg):
    if d >= 0:
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-ss", f"{d:.3f}", "-i", str(src)]
    else:
        cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", str(src), "-vf", f"tpad=start_duration={-d:.3f}",
               "-af", f"adelay={int(-d * 1000)}:all=1"]
    subprocess.run(cmd + ["-f", "mp4", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", str(dst)], check=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import open_clip

    import attempt_clf as ac
    import fetch_clips as fc
    import restore_search as rs
    from yolo_pose_onnx import YoloPoseOnnx
    ffmpeg = shutil.which("ffmpeg")
    det = YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")
    model, _, prep = open_clip.create_model_and_transforms(ac.ARCH, pretrained=ac.WEIGHTS)
    model.eval()
    clips = {}
    for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")):
        clips.setdefault(r["video_url"], r)
    disk = {p.name for p in (ROOT / "data/clips").rglob("*")}
    for name, r in sorted(clips.items()):
        npz = ROOT / "data/attempt_clf/clips_crop" / f"{name}.npz"
        if name in disk or not npz.exists() or (ROOT / "data/crops" / name / "index.csv").exists():
            continue
        hit = fc.search(r["attacker"], r["defender"])
        if not hit or hit[2] > MAX_MIN * 60:
            print(name, "no usable official video", flush=True); continue
        tmp = OUT / f"_tmp_{hit[0]}"
        subprocess.run(["yt-dlp", "-q", "--no-playlist", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                        "-o", f"{tmp}.%(ext)s", f"https://www.youtube.com/watch?v={hit[0]}"])
        got = next(iter(OUT.glob(f"_tmp_{hit[0]}.mp4")), None)
        if got is None:
            print(name, "download failed", flush=True); continue
        ts, X = fingerprints(got, det, model, prep)
        m, d = best_shift(np.load(npz), ts, X)
        if m < MIN_MATCH:
            got.unlink()
            print(name, f"removed: best match {m:.2f} at {d:+.0f} s", flush=True); continue
        dst = OUT / name
        shift_video(got, dst, d, ffmpeg)
        got.unlink()
        check = rs.match(dst, npz, det, model, prep)
        if check < MIN_MATCH:
            dst.unlink()
            print(name, f"removed after shifting: {check:.2f}", flush=True); continue
        print(name, f"KEPT: shifted {d:+.1f} s, match {check:.2f} | {hit[1]} | {hit[3]}", flush=True)


if __name__ == "__main__":
    main()
