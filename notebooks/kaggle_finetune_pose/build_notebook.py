"""Generate finetune.ipynb from the cell sources below (edit here, then re-run).

    python notebooks/kaggle_finetune_pose/build_notebook.py

The ONNX wrapper (yolo_pose_onnx.py, next to this file) is embedded into the notebook
so the notebook stays a single upload. smoke_test.py runs the same cells locally on CPU.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRAPPER_SRC = (HERE / "yolo_pose_onnx.py").read_text(encoding="utf-8")

CELLS = []


def md(s):
    CELLS.append(("markdown", s.strip("\n")))


def code(s):
    CELLS.append(("code", s.strip("\n")))


md(r"""
# RNCV: fine-tune a pose model on grappling data (Kaggle GPU)

**Goal:** RTMO-m loses the second, tangled fighter on the ground. This notebook fine-tunes **YOLO11m-pose** (COCO-17 keypoints)
on close-contact grappling/MMA images so both fighters are found, then exports an **ONNX** file that runs on the laptop CPU
with `onnxruntime` (see `docs/KAGGLE_FINETUNE.md`).

**Data (no UFC footage anywhere):**
- **Harmony4D** (MIT): grappling + MMA sequences, 20 cameras, 2D poses of both people. Only the sampled frames are fetched from
  Hugging Face with HTTP range reads; the 352 GB of zips are never downloaded.
- **VICOS BJJ** (CC BY-NC-SA 4.0): BJJ sparring with both athletes' keypoints. Again only the sampled frames are fetched.

**Splits are by sequence, never by frame.** Harmony4D: the official `test/` sequences are the test set; 3 whole train sequences are
validation. VICOS: sequence 5 (videos 14-15) is test, sequence 3 (videos 9-10) is validation.

**Settings (right sidebar):** Accelerator = **GPU T4 x1**, Internet = **On**. Then **Save Version > Save & Run All (Commit)**.

**Runtime (estimate):** ~30-60 min data fetch + conversion, `TRAIN_HOURS` (default 4 h) training, ~20 min evaluation + export.
About 5-6 of your 30 weekly GPU hours.

**Every cell is safe to re-run:** finished downloads, training and exports are skipped.
""")

code(r'''
# ===================== CONFIG: the only cell you normally edit =====================
import os
ON_KAGGLE = os.path.exists("/kaggle/working")
SMOKE_TEST = os.environ.get("RNCV_SMOKE") == "1"   # tiny CPU run for the local check; stays False on Kaggle
PLAN_ONLY = os.environ.get("RNCV_PLAN_ONLY") == "1"  # True = only list the data and print the subset size

RUN_NAME = "rncv_pose_v1"
BASE_MODEL = "yolo11m-pose.pt"     # COCO-pretrained start (n < s < m < l < x: bigger = slower on the laptop CPU)
TRAIN_HOURS = 4.0                  # hard training time budget (keeps the whole run < 6 h)
EPOCHS = 100                       # only used if TRAIN_HOURS is None
IMGSZ = 640
BATCH = 16                         # fits a 16 GB T4 with yolo11m-pose at 640
DEVICE = 0                         # 0 = one T4. [0, 1] = both T4s (Accelerator "GPU T4 x2"), about 1.7x faster
FORCE_RETRAIN = False              # True = ignore an earlier finished run
SEED = 0

USE_HARMONY4D = True
USE_VICOS = True                   # CC BY-NC-SA: the weights are then non-commercial. False = MIT-only data

H4D_URL = "https://huggingface.co/datasets/Jyun-Ting/Harmony4D/resolve/main/"
H4D_ZIPS = {                       # zip -> kind. Only grappling and MMA; sizes are the full zips (never downloaded)
    "train/02_grappling.zip": "grappling",   # 44.1 GB, 35 sequences
    "train/03_grappling2.zip": "grappling",  # 17.0 GB, 16 sequences
    "train/12_mma.zip": "mma",               # 17.4 GB
    "train/13_mma2.zip": "mma",              # 14.9 GB
    "train/14_mma3.zip": "mma",              # 10.7 GB
    "train/15_mma4.zip": "mma",              # 10.6 GB
    "test/03_grappling2.zip": "grappling",   # 14.6 GB, test sequences
    "test/15_mma4.zip": "mma",               # 2.3 GB, test
    "test/16_mma5.zip": "mma",               # 11.1 GB, test
}
H4D_VAL_SEQS = ["024_grappling", "008_grappling2", "007_mma3"]  # whole train sequences held out for model selection
H4D_ONLY_SEQS = None               # None = all sequences of the zips above
H4D_SPLIT_OVERRIDE = {}            # {sequence: split}, used by the smoke test
H4D_STEP = {"train": {"grappling": 5, "mma": 10},   # every k-th frame (30 fps capture)
            "val": {"grappling": 10, "mma": 15},
            "test": {"grappling": 15, "mma": 30}}
H4D_CAMS_PER_FRAME = {"train": 6, "val": 3, "test": 3}  # random cameras (of 20) per sampled frame

VICOS_ANN_URL = "https://data.vicos.si/datasets/JuiJuitsu/annotations.json"   # 209 MB
VICOS_ZIP_URL = "https://data.vicos.si/datasets/JuiJuitsu/images.zip"         # 10.0 GB, never downloaded whole
VICOS_SPLIT = {"train": [0, 1, 2, 4], "val": [3], "test": [5]}               # sequence ids (see VIDEO_TO_SEQUENCE)
VICOS_STEP = {"train": 15, "val": 60, "test": 30}
VICOS_KPT_THR = 0.3                # VICOS keypoints below this confidence are marked invisible

CROP_CONTEXT = (1.2, 2.5)          # crop around both people with this much context (broadcast-like zoom). None = full frame
MAX_SIDE = 1024                    # stored image size (long side)
JPEG_QUALITY = 92
DL_THREADS = 24
MAX_ITEMS = None                   # cap per (source, split), for quick tests

EVAL_RTMO = True                   # also score today's laptop model (RTMO-m at 0.3 / 0.65) on the same test images
PRED_CONF = 0.25                   # YOLO person-score cutoff for the "both found" metrics
NMS_IOU = 0.65
RTMO_SCORE_THR, RTMO_NMS_THR = 0.3, 0.65

WORK = "/tmp/rncv_pose" if ON_KAGGLE else os.environ.get("RNCV_WORK", "rncv_pose_work")    # big scratch (not saved)
OUT = "/kaggle/working" if ON_KAGGLE else os.environ.get("RNCV_OUT", "rncv_pose_out")      # saved outputs (<20 GB)

if SMOKE_TEST:  # a few images, 1 CPU epoch, tiny model: checks the code path, not the model
    BASE_MODEL, TRAIN_HOURS, EPOCHS, IMGSZ, BATCH, DEVICE = "yolo11n-pose.pt", None, 1, 320, 4, "cpu"
    H4D_ZIPS = {"test/16_mma5.zip": "mma"}
    H4D_SPLIT_OVERRIDE = {"001_mma5": "train", "002_mma5": "val", "003_mma5": "test"}
    H4D_ONLY_SEQS = list(H4D_SPLIT_OVERRIDE)
    MAX_ITEMS, DL_THREADS, EVAL_RTMO = 20, 8, False
    VICOS_ANN_URL = os.environ.get("RNCV_VICOS_ANN", VICOS_ANN_URL)
os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True)
print("Kaggle:", ON_KAGGLE, "| smoke test:", SMOKE_TEST, "| work:", WORK, "| out:", OUT)
''')

code(r'''
# Install + environment checks
import subprocess, sys
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.182", "onnx", "onnxslim",
                    "onnxruntime-gpu"], check=True)
    if EVAL_RTMO:  # --no-deps keeps rtmlib from pulling the CPU-only onnxruntime over the GPU one
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "rtmlib==0.0.16"], check=True)
import requests, torch
try:
    requests.head("https://huggingface.co", timeout=20)
except Exception as e:
    raise SystemExit("No internet. Kaggle: Settings (right sidebar) > Internet = On (needs a phone-verified account).") from e
if ON_KAGGLE and not torch.cuda.is_available():
    raise SystemExit("No GPU. Kaggle: Settings > Accelerator = GPU T4 x1, then run again.")
print("torch", torch.__version__, "| CUDA:", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
''')

md(r"""
## Remote zip reader
Reads the zip's table of contents with HTTP range requests, then fetches single files (one image, one label) on demand.
Hugging Face allows 3000 link lookups per 5 minutes, so each zip's signed download link is looked up once and refreshed only when it expires.
""")

code(r'''
import io, json, gzip, struct, threading, time, zlib, zipfile
import numpy as np

class _RangeFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests (only used to read the zip's table of contents)."""
    def __init__(self, rz):
        self.rz, self.pos = rz, 0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.rz.size + off
        return self.pos
    def readinto(self, b):
        n = min(len(b), self.rz.size - self.pos)
        if n <= 0: return 0
        d = self.rz.get(self.pos, self.pos + n - 1)
        b[:len(d)] = d; self.pos += len(d)
        return len(d)

class RemoteZip:
    def __init__(self, src_url, cache_dir):
        self.src = src_url
        self._local = threading.local()
        self._lock = threading.Lock()
        self._resolve()
        key = src_url.split("/resolve/main/")[-1].replace("/", "__").replace(":", "_")
        cache = os.path.join(cache_dir, key + ".index.json.gz")
        if os.path.exists(cache):
            with gzip.open(cache, "rt") as f: self.index = json.load(f)
        else:
            t0 = time.time()
            zf = zipfile.ZipFile(io.BufferedReader(_RangeFile(self), buffer_size=1 << 20))
            self.index = {i.filename: [i.header_offset, i.compress_size, i.compress_type]
                          for i in zf.infolist() if not i.is_dir()}
            os.makedirs(cache_dir, exist_ok=True)
            with gzip.open(cache, "wt") as f: json.dump(self.index, f)
            print(f"  listed {key}: {len(self.index):,} files in {time.time() - t0:.0f} s")

    def _session(self):
        s = getattr(self._local, "s", None)
        if s is None:
            s = self._local.s = requests.Session()
        return s

    def _resolve(self):
        with self._lock:
            r = requests.head(self.src, allow_redirects=True, timeout=60)
            r.raise_for_status()
            self.url, self.size = r.url, int(r.headers["Content-Length"])

    def get(self, a, b):
        for attempt in range(6):
            try:
                r = self._session().get(self.url, headers={"Range": f"bytes={a}-{b}"}, timeout=120)
                if r.status_code == 206: return r.content
                if r.status_code in (400, 401, 403, 404, 410): self._resolve()   # signed link expired
            except requests.RequestException:
                pass
            time.sleep(min(30, 2 ** attempt))
        raise IOError(f"range {a}-{b} failed for {self.src}")

    def read(self, name):
        off, csize, ctype = self.index[name]
        n = len(name.encode())
        b = self.get(off, off + 30 + n + 512 + csize - 1)        # local header + extra-field slack + data
        assert b[:4] == b"PK\x03\x04", "bad local header"
        ln, lm = struct.unpack("<HH", b[26:30])
        start = 30 + ln + lm
        if start + csize > len(b): b += self.get(off + len(b), off + start + csize - 1)
        data = b[start:start + csize]
        return data if ctype == 0 else zlib.decompress(data, -15)

import pickle
class _NumpyOnly(pickle.Unpickler):
    """Harmony4D .npy files are pickled dicts of arrays. Allow only numpy classes (no arbitrary code)."""
    OK = {"_reconstruct", "ndarray", "dtype", "scalar"}
    def find_class(self, module, name):
        if module.split(".")[0] == "numpy" and name in self.OK:
            import importlib
            if module.startswith("numpy.core") and np.__version__ >= "2":
                module = module.replace("numpy.core", "numpy._core")
            return getattr(importlib.import_module(module), name)
        raise pickle.UnpicklingError(f"blocked {module}.{name}")

def load_npy_dict(b):
    """bytes of an object .npy -> dict {person_id: array}"""
    obj = _NumpyOnly(io.BytesIO(b[b.index(b"\n") + 1:])).load()
    return obj.item() if hasattr(obj, "item") else obj
''')

md(r"""
## Convert to COCO-17 + YOLO labels
- **Harmony4D** 2D poses use the SMPL_45 joint order (24 SMPL joints + nose/eyes/ears/feet/hands). They are projected from the
  3D fit, so occluded joints have positions too (marked visible). Caveat: SMPL hips sit slightly higher and more inward than COCO hips.
- **VICOS** keypoints are already COCO-17 with a confidence; below `VICOS_KPT_THR` they are marked invisible. Boxes come from the keypoints.
- Each image is cropped around both people with random context (`CROP_CONTEXT`), so people appear at broadcast-like sizes.
""")

code(r'''
import cv2
SMPL45_TO_COCO17 = [24, 26, 25, 28, 27, 16, 17, 18, 19, 20, 21, 1, 2, 4, 5, 7, 8]
COCO_FLIP_IDX = [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]
VIDEO_TO_SEQUENCE = {v: s for s, vids in enumerate(
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10], [11, 12, 13], [14, 15]]) for v in vids}  # same as src/vicos_data.py

def h4d_to_coco(j45):
    """[45, 2+] SMPL_45 pixel coords -> [17, 3] (x, y, v), v=2 where finite."""
    j = np.asarray(j45, dtype=np.float64)[SMPL45_TO_COCO17, :2]
    ok = np.isfinite(j).all(1)
    return np.concatenate([np.where(ok[:, None], j, 0), (ok * 2.0)[:, None]], 1)

def vicos_to_coco(pose, thr=VICOS_KPT_THR):
    """VICOS [17, 3] (x, y, conf) -> [17, 3] (x, y, v), or None if the pose is missing."""
    if not pose or len(pose) != 17: return None
    p = np.asarray(pose, dtype=np.float64)
    ok = np.isfinite(p).all(1) & (p[:, 2] >= thr)
    return np.concatenate([np.where(ok[:, None], p[:, :2], 0), (ok * 2.0)[:, None]], 1)

def box_from_kpts(k, pad=0.15, head=0.10):
    v = k[:, 2] > 0
    x0, y0 = k[v, :2].min(0); x1, y1 = k[v, :2].max(0)
    w, h = x1 - x0, y1 - y0
    return np.array([x0 - pad * w, y0 - (pad + head) * h, x1 + pad * w, y1 + pad * h])

def crop_window(boxes, W, H, rng, context=CROP_CONTEXT, aspect=16 / 9):
    """Window around the union of all boxes, `context` x larger, broadcast aspect, randomly shifted, clipped to the image."""
    if context is None: return 0, 0, W, H
    u = np.array([min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)])
    cx, cy = (u[0] + u[2]) / 2, (u[1] + u[3]) / 2
    s = rng.uniform(*context)
    w, h = (u[2] - u[0]) * s, (u[3] - u[1]) * s
    w, h = max(w, h * aspect), max(h, w / aspect)
    w, h = min(w, W), min(h, H)
    cx += rng.uniform(-0.25, 0.25) * max(0.0, w - (u[2] - u[0]))
    cy += rng.uniform(-0.25, 0.25) * max(0.0, h - (u[3] - u[1]))
    x0 = int(np.clip(cx - w / 2, 0, W - w)); y0 = int(np.clip(cy - h / 2, 0, H - h))
    return x0, y0, int(x0 + w), int(y0 + h)

def finalize(img, people, name, split, meta, rng):
    """Crop + resize, write image, YOLO label and meta json. people = [(kpts[17,3], box[4]), ...] in img pixels."""
    H, W = img.shape[:2]
    boxes = [np.clip(b, [0, 0, 0, 0], [W, H, W, H]) for _, b in people]
    x0, y0, x1, y1 = crop_window(boxes, W, H, rng)
    crop = img[y0:y1, x0:x1]
    s = min(1.0, MAX_SIDE / max(crop.shape[:2]))
    if s < 1: crop = cv2.resize(crop, (round(crop.shape[1] * s), round(crop.shape[0] * s)), interpolation=cv2.INTER_AREA)
    h, w = crop.shape[:2]
    lines, gts = [], []
    for (k, b0), b in zip(people, boxes):
        k = k.copy(); k[:, :2] = (k[:, :2] - [x0, y0]) * s
        inside = (k[:, 0] >= 0) & (k[:, 0] < w) & (k[:, 1] >= 0) & (k[:, 1] < h)
        k[~inside | (k[:, 2] == 0)] = 0
        bb = np.clip((np.asarray(b0, float) - [x0, y0, x0, y0]) * s, 0, [w, h, w, h])
        full = max(1e-6, (b0[2] - b0[0]) * (b0[3] - b0[1]) * s * s)
        if (bb[2] - bb[0]) * (bb[3] - bb[1]) < 0.25 * full or (k[:, 2] > 0).sum() < 3:
            continue   # person mostly outside the crop
        cx, cy, bw, bh = (bb[0] + bb[2]) / 2 / w, (bb[1] + bb[3]) / 2 / h, (bb[2] - bb[0]) / w, (bb[3] - bb[1]) / h
        kn = [f"{x / w:.5f} {y / h:.5f} {int(v)}" for x, y, v in k]
        lines.append(f"0 {cx:.5f} {cy:.5f} {bw:.5f} {bh:.5f} " + " ".join(kn))
        gts.append({"kpts": k.round(2).tolist(), "box": bb.round(2).tolist()})
    if not lines: return False
    paths = {d: os.path.join(WORK, "yolo", d, split, name + ext)
             for d, ext in (("images", ".jpg"), ("labels", ".txt"), ("meta", ".json"))}
    for p in paths.values(): os.makedirs(os.path.dirname(p), exist_ok=True)
    cv2.imwrite(paths["images"], crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    with open(paths["labels"], "w") as f: f.write("\n".join(lines) + "\n")
    with open(paths["meta"], "w") as f: json.dump({**meta, "img": paths["images"], "gt": gts}, f)  # written last = done
    return True

def item_done(it):
    return os.path.exists(os.path.join(WORK, "yolo", "meta", it["split"], it["name"] + ".json")) or \
           os.path.exists(os.path.join(WORK, "yolo", "skipped", it["name"]))

def mark_skipped(it):
    os.makedirs(os.path.join(WORK, "yolo", "skipped"), exist_ok=True)
    open(os.path.join(WORK, "yolo", "skipped", it["name"]), "w").close()

def item_rng(it):
    return np.random.default_rng([SEED, zlib.crc32(it["name"].encode())])

def process_h4d(it, zips):
    rz = zips[it["zip"]]
    img = cv2.imdecode(np.frombuffer(rz.read(it["img"]), np.uint8), cv2.IMREAD_REDUCED_COLOR_2)  # 4K -> half size
    s = 0.5
    poses = load_npy_dict(rz.read(it["p2d"]))
    bbox = load_npy_dict(rz.read(it["bbox"])) if it["bbox"] in rz.index else {}
    people = []
    for pid in sorted(poses):
        k = h4d_to_coco(np.asarray(poses[pid], float) * s)
        if (k[:, 2] > 0).sum() < 3: continue
        b = np.asarray(bbox[pid], float) * s if pid in bbox else box_from_kpts(k)
        people.append((k, b))
    if len(people) < len(poses) or not people: return False
    return finalize(img, people, it["name"], it["split"],
                    {"source": "h4d", "subset": f"h4d_{it['kind']}", "seq": it["seq"]}, item_rng(it))

def process_vicos(it, zips):
    rec = it["rec"]
    people = []
    for key in ("pose1", "pose2"):
        k = vicos_to_coco(rec.get(key))
        if k is None or (k[:, 2] > 0).sum() < 6: return False   # need both athletes labeled, else skip the frame
        people.append((k, box_from_kpts(k)))
    img = cv2.imdecode(np.frombuffer(zips["vicos"].read(rec["image"] + ".jpg"), np.uint8), cv2.IMREAD_COLOR)
    return finalize(img, people, it["name"], it["split"],
                    {"source": "vicos", "subset": "vicos_bjj", "seq": it["seq"]}, item_rng(it))
''')

md(r"""
## Choose the subset (split by sequence)
Lists each zip's table of contents (cached in `WORK/index`), then samples frames and cameras. Prints how many images each split gets.
""")

code(r'''
import re
from collections import Counter, defaultdict
ZIPS, ITEMS = {}, []

def cap(items):
    if MAX_ITEMS is None or len(items) <= MAX_ITEMS: return items
    return [items[i] for i in np.linspace(0, len(items) - 1, MAX_ITEMS).astype(int)]

if USE_HARMONY4D:
    pat = re.compile(r"^([^/]+)/([^/]+)/exo/(cam\d+)/images/(\d+)\.jpg$")
    for zkey, kind in H4D_ZIPS.items():
        print("Harmony4D", zkey)
        rz = ZIPS[zkey] = RemoteZip(H4D_URL + zkey, os.path.join(WORK, "index"))
        frames = defaultdict(lambda: defaultdict(list))  # seq -> frame -> cams
        top_of = {}
        for name in rz.index:
            m = pat.match(name)
            if not m: continue
            top, seq, cam, fr = m.groups()
            if H4D_ONLY_SEQS is not None and seq not in H4D_ONLY_SEQS: continue
            if f"{top}/{seq}/processed_data/poses2d/{cam}/{fr}.npy" not in rz.index: continue
            frames[seq][fr].append(cam); top_of[seq] = top
        by_split = defaultdict(list)
        for seq in sorted(frames):
            split = H4D_SPLIT_OVERRIDE.get(seq) or ("test" if zkey.startswith("test/") else
                                                    "val" if seq in H4D_VAL_SEQS else "train")
            frs = sorted(frames[seq])
            for fr in frs[::H4D_STEP[split][kind]]:
                cams = sorted(frames[seq][fr])
                rng = np.random.default_rng([SEED, zlib.crc32(f"{seq}/{fr}".encode())])
                for cam in rng.choice(cams, min(H4D_CAMS_PER_FRAME[split], len(cams)), replace=False):
                    base = f"{top_of[seq]}/{seq}"
                    by_split[split].append({"src": "h4d", "zip": zkey, "kind": kind, "seq": seq, "split": split,
                        "name": f"h4d_{seq}_{cam}_{fr}", "img": f"{base}/exo/{cam}/images/{fr}.jpg",
                        "p2d": f"{base}/processed_data/poses2d/{cam}/{fr}.npy",
                        "bbox": f"{base}/processed_data/bbox/{cam}/{fr}.npy"})
        for split, its in by_split.items():
            ITEMS += cap(its)

if USE_VICOS:
    ann_path = VICOS_ANN_URL if os.path.exists(VICOS_ANN_URL) else os.path.join(WORK, "vicos_annotations.json")
    if not os.path.exists(ann_path):
        with requests.get(VICOS_ANN_URL, stream=True, timeout=120) as r, open(ann_path + ".part", "wb") as f:
            r.raise_for_status()
            for chunk in r.iter_content(1 << 20): f.write(chunk)
        os.replace(ann_path + ".part", ann_path)
    with open(ann_path) as f: vicos_ann = json.load(f)
    print("VICOS", len(vicos_ann), "annotated frames")
    ZIPS["vicos"] = RemoteZip(VICOS_ZIP_URL, os.path.join(WORK, "index"))
    seq_split = {s: sp for sp, seqs in VICOS_SPLIT.items() for s in seqs}
    by_split = defaultdict(list)
    for rec in vicos_ann:
        seq = VIDEO_TO_SEQUENCE[int(rec["image"][:2])]
        split = seq_split.get(seq)
        if split is None or int(rec["frame"]) % VICOS_STEP[split] or rec["image"] + ".jpg" not in ZIPS["vicos"].index:
            continue
        by_split[split].append({"src": "vicos", "seq": f"vicos_seq{seq}", "split": split,
                                "name": f"vicos_{rec['image']}", "rec": rec})
    for split, its in by_split.items():
        ITEMS += cap(its)

def nbytes(it):
    if it["src"] == "vicos": return ZIPS["vicos"].index[it["rec"]["image"] + ".jpg"][1]
    return sum(ZIPS[it["zip"]].index.get(it[key], [0, 0])[1] for key in ("img", "p2d", "bbox"))

tab = Counter((it["split"], it["src"] if it["src"] == "vicos" else "h4d_" + it["kind"]) for it in ITEMS)
for (split, src), n in sorted(tab.items()):
    print(f"  {split:5s} {src:14s} {n:7,d} images")
seqs = {sp: {it["seq"] for it in ITEMS if it["split"] == sp} for sp in ("train", "val", "test")}
assert not (seqs["train"] & seqs["val"]) and not (seqs["train"] & seqs["test"]) and not (seqs["val"] & seqs["test"]), \
    "a sequence is in two splits"
print(f"total {len(ITEMS):,} images from {sum(len(v) for v in seqs.values())} sequences; "
      f"download ~{sum(nbytes(it) for it in ITEMS) / 1e9:.1f} GB (estimate), stored ~{len(ITEMS) * 0.12 / 1e3:.1f} GB (estimate)")
''')

code(r'''
# Fetch + convert (threaded). Re-running skips finished images.
from concurrent.futures import ThreadPoolExecutor, as_completed
def run_item(it):
    if item_done(it): return "done"
    try:
        ok = (process_vicos if it["src"] == "vicos" else process_h4d)(it, ZIPS)
        if not ok: mark_skipped(it)
        return "ok" if ok else "skipped"
    except Exception as e:
        return f"error: {type(e).__name__}: {e}"

if PLAN_ONLY:
    print("PLAN_ONLY: stopping before the download.")
else:
    t0, stats, errors = time.time(), Counter(), []
    with ThreadPoolExecutor(DL_THREADS) as ex:
        futs = [ex.submit(run_item, it) for it in ITEMS]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result(); stats[r.split(":")[0]] += 1
            if r.startswith("error"): errors.append(r)
            if i % 1000 == 0 or i == len(futs):
                print(f"  {i:,}/{len(futs):,} {dict(stats)}  {time.time() - t0:.0f} s", flush=True)
    for e in errors[:5]: print(" ", e)
    assert stats["error"] <= 0.05 * len(ITEMS), "more than 5% of downloads failed; re-run this cell"

    yolo_dir = os.path.join(WORK, "yolo")
    data_yaml = os.path.join(WORK, "data.yaml")
    with open(data_yaml, "w") as f:
        f.write(f"path: {yolo_dir}\ntrain: images/train\nval: images/val\ntest: images/test\n"
                f"kpt_shape: [17, 3]\nflip_idx: {COCO_FLIP_IDX}\nnames:\n  0: person\n")
    RECORDS = {}
    for split in ("train", "val", "test"):
        d = os.path.join(yolo_dir, "meta", split)
        RECORDS[split] = [json.load(open(os.path.join(d, n))) for n in sorted(os.listdir(d))] if os.path.isdir(d) else []
        print(f"{split}: {len(RECORDS[split]):,} images, {Counter(r['subset'] for r in RECORDS[split])}")
    # one image list per test subset, for per-subset AP
    TEST_LISTS = {}
    for sub in sorted({r["subset"] for r in RECORDS["test"]}):
        TEST_LISTS[sub] = os.path.join(WORK, f"test_{sub}.txt")
        with open(TEST_LISTS[sub], "w") as f: f.write("\n".join(r["img"] for r in RECORDS["test"] if r["subset"] == sub) + "\n")
''')

code(r'''
# Look at a few training images with their labels (saved to OUT/previews). Red/blue = the two people.
SKELETON = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
def draw_people(img, people, colors=((0, 0, 255), (255, 0, 0), (0, 200, 0), (0, 200, 200))):
    for i, k in enumerate(people):
        c = colors[i % len(colors)]
        for a, b in SKELETON:
            if k[a][2] > 0 and k[b][2] > 0:
                cv2.line(img, (int(k[a][0]), int(k[a][1])), (int(k[b][0]), int(k[b][1])), c, 2)
        for x, y, v in k:
            if v > 0: cv2.circle(img, (int(x), int(y)), 3, c, -1)
    return img
if not PLAN_ONLY:
    os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)
    pick = np.random.default_rng(SEED).choice(len(RECORDS["train"]), min(6, len(RECORDS["train"])), replace=False)
    for i in pick:
        r = RECORDS["train"][i]
        im = draw_people(cv2.imread(r["img"]), [g["kpts"] for g in r["gt"]])
        cv2.imwrite(os.path.join(OUT, "previews", os.path.basename(r["img"])), im)
    try:
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, 3, figsize=(15, 6))
        for ax, i in zip(axs.flat, pick):
            ax.imshow(cv2.imread(os.path.join(OUT, "previews", os.path.basename(RECORDS["train"][i]["img"])))[:, :, ::-1])
            ax.set_title(RECORDS["train"][i]["subset"]); ax.axis("off")
        plt.tight_layout(); plt.show()
    except ImportError:
        pass
''')

md(r"""
## Fine-tune
Starts from the COCO-pretrained YOLO11m-pose and trains for `TRAIN_HOURS` (Ultralytics stops on time and fits the learning-rate schedule
to it). If the session dies, re-running this cell resumes from `last.pt`. The best epoch on the validation sequences is kept as `best.pt`.
""")

code(r'''
from ultralytics import YOLO
RUN_DIR = os.path.join(OUT, "runs", RUN_NAME)
BEST, LAST, DONE = (os.path.join(RUN_DIR, "weights", "best.pt"), os.path.join(RUN_DIR, "weights", "last.pt"),
                    os.path.join(RUN_DIR, "TRAINING_DONE"))
if PLAN_ONLY:
    pass
elif os.path.exists(DONE) and not FORCE_RETRAIN:
    print("Training already finished:", BEST)
elif os.path.exists(LAST) and not FORCE_RETRAIN:
    print("Resuming", LAST)
    YOLO(LAST).train(resume=True)
    open(DONE, "w").close()
else:
    t0 = time.time()
    YOLO(BASE_MODEL).train(
        data=data_yaml, imgsz=IMGSZ, batch=BATCH, device=DEVICE, workers=4, seed=SEED,
        time=TRAIN_HOURS, epochs=EPOCHS, patience=100,
        optimizer="AdamW", lr0=5e-4, cos_lr=True, warmup_epochs=1,
        degrees=15, fliplr=0.5, mosaic=1.0, scale=0.5,       # bodies lie at all angles on the ground
        project=os.path.join(OUT, "runs"), name=RUN_NAME, exist_ok=True, plots=True, verbose=False)
    open(DONE, "w").close()
    print(f"training took {(time.time() - t0) / 3600:.2f} h")
''')

md(r"""
## Evaluate on held-out sequences
Same test images for every model:
- **base** = COCO YOLO11m-pose before fine-tuning, **finetuned** = this run, **finetuned_onnx** = the exported file through the laptop wrapper
  (should match finetuned), **rtmo_m** = today's laptop model (RTMO-m at score 0.3 / NMS 0.65).
- **both_found**: share of 2-person images where *both* people are matched by a prediction with OKS >= 0.5 (OKS = COCO keypoint similarity, 0-1).
- **both_upper**: both matched predictions have >= 5 of 7 upper-body joints at confidence >= 0.3 (the FINDINGS.md metric).
- **pck10**: share of labeled joints predicted within 10% of the person's box size (a missed person counts as all joints wrong).
- **extra_dets**: unmatched detections per image (unlabeled bystanders count here too).
- **AP** (Ultralytics, OKS mAP50-95): bystanders in Harmony4D images are unlabeled, so a model that finds them is penalized. VICOS labels come
  from the authors' detector, so VICOS scores measure agreement with it, not ground truth.
""")

code(r'''
COCO_SIGMAS = np.array([.26, .25, .25, .35, .35, .79, .79, .72, .72, .62, .62, 1.07, 1.07, .87, .87, .89, .89]) / 10
UPPER = [0, 5, 6, 7, 8, 9, 10]

def oks(gt, box, pred):
    g = np.asarray(gt); vis = g[:, 2] > 0
    if not vis.any(): return 0.0
    area = max(1.0, (box[2] - box[0]) * (box[3] - box[1])) * 0.53   # box area -> approx. segment area (COCO convention)
    d2 = ((g[:, :2] - pred[:, :2]) ** 2).sum(1)
    return float(np.exp(-d2 / (2 * area * (2 * COCO_SIGMAS) ** 2 + 1e-9))[vis].mean())

def greedy_match(gts, preds):
    """[(gt_i, pred_j, oks)] one-to-one, highest OKS first (with 2 people, greedy = optimal in practice)."""
    if not gts or not len(preds): return []
    M = np.array([[oks(g["kpts"], g["box"], p) for p in preds] for g in gts])
    out, used_g, used_p = [], set(), set()
    for gi, pj in zip(*np.unravel_index(np.argsort(-M, axis=None), M.shape)):
        if gi in used_g or pj in used_p or M[gi, pj] <= 0: continue
        out.append((int(gi), int(pj), float(M[gi, pj]))); used_g.add(gi); used_p.add(pj)
    return out

def evaluate(predict, records, label):
    """predict(img_bgr) -> (kps [N,17,2], scores [N,17]). Returns {subset: metrics}."""
    acc = defaultdict(lambda: defaultdict(list))
    t_inf = []
    for r in records:
        img = cv2.imread(r["img"])
        t0 = time.perf_counter(); kps, scs = predict(img); t_inf.append(time.perf_counter() - t0)
        preds = [np.concatenate([np.asarray(k)[:, :2], np.asarray(s)[:, None]], 1) for k, s in zip(kps, scs)]
        m = greedy_match(r["gt"], preds)
        good = [(gi, pj) for gi, pj, o in m if o >= 0.5]
        for a in (acc[r["subset"]], acc["all"]):
            if len(r["gt"]) == 2:
                a["both_found"].append(len(good) == 2)
                a["both_upper"].append(len(good) == 2 and all((preds[pj][UPPER, 2] >= 0.3).sum() >= 5 for _, pj in good))
            a["extra_dets"].append(len(preds) - len(m))
            a["mean_oks"] += [o for *_, o in m] + [0.0] * (len(r["gt"]) - len(m))
            pm = {gi: pj for gi, pj, _ in m}
            for gi, g in enumerate(r["gt"]):
                gk = np.asarray(g["kpts"]); vis = gk[:, 2] > 0
                thr = 0.1 * max(g["box"][2] - g["box"][0], g["box"][3] - g["box"][1])
                if gi in pm:
                    d = np.linalg.norm(gk[:, :2] - preds[pm[gi]][:, :2], axis=1)
                    a["pck10"] += list(d[vis] <= thr)
                else:
                    a["pck10"] += [False] * int(vis.sum())
    res = {sub: {k: round(float(np.mean(v)), 4) for k, v in a.items()} | {"n_images": len(a["extra_dets"])}
           for sub, a in acc.items()}
    res["all"]["ms_per_image"] = round(1000 * float(np.median(t_inf)), 1)
    print(f"{label:16s} " + "  ".join(f"{s}: found {m['both_found']:.0%} upper {m['both_upper']:.0%} pck {m['pck10']:.0%}"
                                      for s, m in res.items() if "both_found" in m))
    return res

def yolo_predictor(model):
    def predict(img):
        r = model.predict(img, imgsz=IMGSZ, conf=PRED_CONF, iou=NMS_IOU, device=DEVICE, verbose=False)[0]
        if r.keypoints is None or not len(r.keypoints): return np.zeros((0, 17, 2)), np.zeros((0, 17))
        k = r.keypoints.data.cpu().numpy()
        return k[..., :2], k[..., 2]
    return predict

def ultralytics_ap(weights):
    out = {}
    for sub, lst in TEST_LISTS.items():
        yml = os.path.join(WORK, f"test_{sub}.yaml")
        with open(yml, "w") as f:
            f.write(f"path: {os.path.join(WORK, 'yolo')}\ntrain: {lst}\nval: {lst}\n"
                    f"kpt_shape: [17, 3]\nflip_idx: {COCO_FLIP_IDX}\nnames:\n  0: person\n")
        m = YOLO(weights).val(data=yml, split="val", imgsz=IMGSZ, batch=BATCH, device=DEVICE, plots=False, verbose=False,
                              project=os.path.join(WORK, "val_runs"), name=sub, exist_ok=True)
        out[sub] = {"pose_AP50_95": round(float(m.pose.map), 4), "pose_AP50": round(float(m.pose.map50), 4),
                    "box_AP50_95": round(float(m.box.map), 4)}
    return out

METRICS = {"config": {k: v for k, v in dict(RUN_NAME=RUN_NAME, BASE_MODEL=BASE_MODEL, TRAIN_HOURS=TRAIN_HOURS, IMGSZ=IMGSZ,
                                             USE_HARMONY4D=USE_HARMONY4D, USE_VICOS=USE_VICOS, PRED_CONF=PRED_CONF).items()},
           "n_images": {s: len(RECORDS.get(s, [])) for s in ("train", "val", "test")} if not PLAN_ONLY else {}}
if not PLAN_ONLY:
    METRICS["both_found_etc"] = {
        "base": evaluate(yolo_predictor(YOLO(BASE_MODEL)), RECORDS["test"], "base"),
        "finetuned": evaluate(yolo_predictor(YOLO(BEST)), RECORDS["test"], "finetuned")}
    if EVAL_RTMO:
        from rtmlib import RTMO
        rtmo = RTMO(onnx_model="https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/"
                               "rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip",
                    model_input_size=(640, 640), backend="onnxruntime",
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    score_thr=RTMO_SCORE_THR, nms_thr=RTMO_NMS_THR)
        METRICS["both_found_etc"]["rtmo_m"] = evaluate(lambda im: rtmo(im), RECORDS["test"], "rtmo_m (laptop)")
    METRICS["ap"] = {"base": ultralytics_ap(BASE_MODEL), "finetuned": ultralytics_ap(BEST)}
    print(json.dumps(METRICS["ap"], indent=1))
''')

md(r"""
## Export to ONNX + check it matches
The ONNX file runs on the laptop with `onnxruntime` through `yolo_pose_onnx.py` (written to the output folder too).
The check runs the ONNX file through that same wrapper on the test images; its scores should match **finetuned** above.
""")

code("WRAPPER_SRC = " + repr(WRAPPER_SRC) + "\n" + r'''
import shutil, importlib
wrapper_path = os.path.join(OUT, "yolo_pose_onnx.py")
with open(wrapper_path, "w") as f: f.write(WRAPPER_SRC)
sys.path.insert(0, OUT)
import yolo_pose_onnx; importlib.reload(yolo_pose_onnx)
ONNX_OUT = os.path.join(OUT, f"{RUN_NAME}.onnx")
if not PLAN_ONLY:
    if not os.path.exists(ONNX_OUT) or os.path.getmtime(ONNX_OUT) < os.path.getmtime(BEST):
        exported = YOLO(BEST).export(format="onnx", imgsz=IMGSZ, opset=17, simplify=True, dynamic=False, half=False)
        shutil.copy(exported, ONNX_OUT)
    print("ONNX:", ONNX_OUT, f"{os.path.getsize(ONNX_OUT) / 1e6:.0f} MB")
    onnx_model = yolo_pose_onnx.YoloPoseOnnx(ONNX_OUT, device="cuda" if torch.cuda.is_available() else "cpu")
    METRICS["both_found_etc"]["finetuned_onnx"] = evaluate(
        lambda im: onnx_model(im, nms_thr=NMS_IOU, score_thr=PRED_CONF), RECORDS["test"], "finetuned_onnx")
    a, b = METRICS["both_found_etc"]["finetuned"]["all"], METRICS["both_found_etc"]["finetuned_onnx"]["all"]
    gap = abs(a["both_found"] - b["both_found"])
    print(f"ONNX vs PyTorch 'both found' gap: {gap:.1%}", "(OK)" if gap <= 0.03 else "(CHECK: larger than 3 points)")
''')

code(r'''
# Summary + files to download (Output tab, or /kaggle/working in the file browser)
if not PLAN_ONLY:
    with open(os.path.join(OUT, f"{RUN_NAME}_metrics.json"), "w") as f: json.dump(METRICS, f, indent=1)
    rows = []
    for model_name, res in METRICS["both_found_etc"].items():
        for sub, m in res.items():
            if "both_found" in m:
                ap = METRICS["ap"].get(model_name, {}).get(sub, {}).get("pose_AP50_95", "")
                rows.append(f"| {model_name} | {sub} | {m['n_images']} | {m['both_found']:.1%} | {m['both_upper']:.1%} | "
                            f"{m['pck10']:.1%} | {m['extra_dets']:.2f} | {ap} |")
    table = ("| model | test subset | images | both found | both upper OK | PCK@0.1 | extra dets/img | pose AP |\n"
             "|---|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    with open(os.path.join(OUT, f"{RUN_NAME}_results.md"), "w") as f: f.write(table + "\n")
    print(table)
    print("\nDownload these into the RNCV repo:")
    for p in (ONNX_OUT, wrapper_path, os.path.join(OUT, f"{RUN_NAME}_metrics.json"), os.path.join(OUT, f"{RUN_NAME}_results.md"), BEST):
        print(f"  {p}  ({os.path.getsize(p) / 1e6:.1f} MB)")
''')


def build():
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "kaggle": {"accelerator": "nvidiaTeslaT4", "isInternetEnabled": True, "isGpuEnabled": True},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    for i, (kind, src) in enumerate(CELLS):
        lines = src.split("\n")
        cell = {"cell_type": kind, "id": f"cell-{i:02d}", "metadata": {},
                "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        nb["cells"].append(cell)
    out = HERE / "finetune.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out, len(CELLS), "cells")


if __name__ == "__main__":
    build()
