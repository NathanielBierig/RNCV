"""RNCV "test the detector" app: a local web app (http://localhost:8765). Nothing leaves the laptop.

    python -I tools/app/serve.py          (the clip venv: open_clip, torch, onnxruntime, sklearn, cv2)

Drop a fight clip on the page. The video plays straight from your disk in the browser. A copy goes to this local
server (data/app_uploads/, git-ignored), which runs the real attempt detector: fighter crop -> CLIP image features
at 2 frames per second -> past-context features -> logistic regression trained on every labeled fight (detector v2,
research/attempt_clf/detector_v2.py). The page then plays the clip with the detector timeline, and you press keys
for what you see (arm under the chin, figure-four, ...) to drive the finish model and the defender's HP live
(tools/app/model.json, exported by export_model.py).
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
UPLOADS = ROOT / "data/app_uploads"
DEMOS = ROOT / "data/clips/test_pool"     # clips never used for training (e.g. pre-2018 fights, outside the study)
sys.argv.append("--crop")
sys.path.insert(0, str(ROOT / "research/attempt_clf"))
sys.path.insert(0, str(ROOT / "src"))
WINDOW_S = 120.0               # analyse 2 minutes from the chosen start (the page sends the start time)
FPS_S = 2.0
STATE = {"progress": "", "clf": None, "clip": None}


def train_detector(exclude=frozenset()):
    """Detector v2 on every labeled fight except any that also sit in the test pool (trained once at startup)."""
    import detector_v2 as d2
    from sklearn.linear_model import LogisticRegression
    X, y, fight, clip, _ = d2.load("_crop")
    keep = ~np.isin(fight, list(exclude))
    clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced").fit(d2.context(X, clip)[keep], y[keep])
    return clf, d2, len(np.unique(fight[keep]))


def fight_of(clip_name):
    import csv
    for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")):
        if r["video_url"] == clip_name:
            return r["fight_id"]
    return None


def load_clip_model():
    import open_clip
    from yolo_pose_onnx import YoloPoseOnnx
    model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model.eval()
    return model, prep, YoloPoseOnnx(ROOT / "models/rncv_pose_v1.onnx")


def analyse(path, start=0.0):
    import attempt_clf as ac
    import torch
    from PIL import Image
    if STATE["clip"] is None:
        STATE["progress"] = "loading image model"
        STATE["clip"] = load_clip_model()
    model, prep, det = STATE["clip"]
    clf, d2, _ = STATE["clf"]
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    end = start + WINDOW_S
    if start > 0:
        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    step, i, batch, ts, feats, t0 = max(1, int(round(fps / FPS_S))), 0, [], [], [], time.time()
    while True:
        ok = cap.grab()
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if not ok or t > end:
            break
        if t < start:
            continue
        if i % step == 0:
            _, f = cap.retrieve()
            batch.append(prep(Image.fromarray(cv2.cvtColor(ac.pair_crop(det, f), cv2.COLOR_BGR2RGB))))
            ts.append(t)
            if len(batch) == 32:
                with torch.no_grad():
                    e = model.encode_image(torch.stack(batch)).float()
                feats.append((e / e.norm(dim=-1, keepdim=True)).numpy()); batch = []
                done = (t - start) / WINDOW_S
                eta = (time.time() - t0) / max(0.01, done) * (1 - done)
                STATE["progress"] = f"analysing {100 * done:.0f}% (about {eta / 60:.1f} min left)"
        i += 1
    if batch:
        with torch.no_grad():
            e = model.encode_image(torch.stack(batch)).float()
        feats.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    cap.release()
    X = np.concatenate(feats)
    p = clf.predict_proba(d2.context(X, np.zeros(len(X), int)))[:, 1]
    p = np.convolve(p, np.ones(5) / 5, mode="same")               # ~2 s smoothing, as in the reports
    STATE["progress"] = "done"
    return {"t": [round(float(x), 2) for x in ts], "p": [round(float(x), 3) for x in p]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self.send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/model.json":
            return self.send(200, (HERE / "model.json").read_bytes())
        if u.path == "/rncv_model.js":
            return self.send(200, (HERE / "rncv_model.js").read_bytes(), "text/javascript; charset=utf-8")
        if u.path == "/progress":
            return self.send(200, {"progress": STATE["progress"]})
        if u.path == "/info":
            return self.send(200, {"fights": STATE["clf"][2],
                                   "demos": sorted(p.name for p in DEMOS.glob("*") if p.is_file())})
        if u.path.startswith("/clip/"):                    # demo clips, streamed with Range so the player can seek
            f = DEMOS / Path(u.path[6:]).name
            if not f.exists():
                return self.send(404, {"error": "no such demo"})
            size, rng = f.stat().st_size, self.headers.get("Range")
            a, b = 0, size - 1
            if rng and rng.startswith("bytes="):
                lo, _, hi = rng[6:].partition("-")
                a = int(lo or 0); b = min(size - 1, int(hi) if hi else min(size - 1, a + (8 << 20)))
            with open(f, "rb") as fh:
                fh.seek(a); data = fh.read(b - a + 1)
            self.send_response(206 if rng else 200)
            self.send_header("Content-Type", "video/webm" if f.suffix == ".webm" else "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(data)))
            if rng:
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.end_headers()
            return self.wfile.write(data)
        self.send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/analyze_demo":                      # a demo clip already on the laptop: no upload
            f = DEMOS / Path(parse_qs(u.query).get("name", [""])[0]).name
            STATE["progress"] = "analysing 0%"
            try:
                return self.send(200, analyse(f, float(parse_qs(u.query).get("start", ["0"])[0])))
            except Exception as e:
                STATE["progress"] = f"error: {e}"
                return self.send(500, {"error": str(e)})
        if u.path != "/analyze":
            return self.send(404, {"error": "not found"})
        name = Path(parse_qs(u.query).get("name", ["clip.mp4"])[0]).name
        n = int(self.headers.get("Content-Length", 0))
        UPLOADS.mkdir(parents=True, exist_ok=True)
        dst = UPLOADS / name
        with open(dst, "wb") as fh:                      # stream to disk (clips can be hundreds of MB)
            left = n
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left))
                if not chunk:
                    break
                fh.write(chunk); left -= len(chunk)
        STATE["progress"] = "analysing 0%"
        try:
            self.send(200, analyse(dst, float(parse_qs(u.query).get("start", ["0"])[0])))
        except Exception as e:                             # report, don't crash the server
            STATE["progress"] = f"error: {e}"
            self.send(500, {"error": str(e)})


def main():
    print("training the detector on the labeled fights...", flush=True)
    pool = {p.name for p in DEMOS.glob("*")} if DEMOS.exists() else set()
    STATE["clf"] = train_detector({fight_of(n) for n in pool} - {None})     # once: test-pool fights never train it
    print(f"ready: open http://localhost:8765  (detector trained on {STATE['clf'][2]} fights; Ctrl+C to stop)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()


if __name__ == "__main__":
    main()
