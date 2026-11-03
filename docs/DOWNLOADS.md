# Downloads

Copy-paste commands for every dataset and model in this project. Run them from the project root.
Sizes and licenses were checked on 2026-10-18. "Can use?" assumes a non-commercial hobby/portfolio project.

| # | What | Size | License | Can use? | Status |
|---|---|---|---|---|---|
| 1 | VICOS BJJ annotations.json (keypoints + labels) | 209 MB | CC BY-NC-SA 4.0 | Yes (non-commercial, credit, share-alike) | **Already downloaded** to `data/raw/vicos/` |
| 2 | VICOS BJJ images.zip | **10.0 GB** | CC BY-NC-SA 4.0 | Yes (as above) | Not downloaded. Only needed to re-run pose models (Kaggle) |
| 3 | HF carlosj934/BJJ_Positions_Submissions | ~260 KB (1 clip) | MIT | Yes | Optional: schema reference only |
| 4 | Roboflow FightersMMA (fighter boxes) | ~2k images | CC BY 4.0 | Yes | Needs a free Roboflow account (steps below) |
| 5 | Mendeley MMA Fighter Detection | 5,106 images | CC BY-NC-SA 4.0 | Non-commercial only | Optional |
| 6 | YOLO11-pose weights (n / s / m) | 6 / 20 / 42 MB | **AGPL-3.0** | Yes, but code you publish must be AGPL too | Auto-downloads inside the Kaggle notebook |
| 7 | RTMO-m / RTMO-l ONNX (via rtmlib) | 83 / 163 MB | Apache-2.0 (MMPose, rtmlib) | Yes | Auto-downloads inside the Kaggle notebook |

## 1. VICOS annotations (done)

```bash
mkdir -p data/raw/vicos && curl -L --fail -o data/raw/vicos/annotations.json https://data.vicos.si/datasets/JuiJuitsu/annotations.json
```

PowerShell equivalent:

```powershell
New-Item -ItemType Directory -Force data/raw/vicos; Invoke-WebRequest https://data.vicos.si/datasets/JuiJuitsu/annotations.json -OutFile data/raw/vicos/annotations.json
```

## 2. VICOS images (10 GB): you only need this for the Kaggle notebook

Don't download this to the laptop unless you want to. The easier route is to have Kaggle fetch it straight into a notebook
(see "Kaggle steps" in the README). If you still want it locally (`-C -` resumes an interrupted download):

```bash
curl -L --fail -C - -o data/raw/vicos/images.zip https://data.vicos.si/datasets/JuiJuitsu/images.zip
```

Citation (required by the license): Hudovernik & Skočaj, "Video-Based Detection of Combat Positions and Automatic Scoring in Jiu-jitsu", MMSports'22 (ACM MM workshop).

## 3. Hugging Face BJJ clip (optional)

```bash
mkdir -p data/raw/hf_bjj && curl -L --fail -o data/raw/hf_bjj/ClosedGuard1_compressed.mp4 "https://huggingface.co/datasets/carlosj934/BJJ_Positions_Submissions/resolve/main/bjj_dataset/closed_guard/ClosedGuard1_compressed.mp4"
```

## 4. Roboflow FightersMMA (needed in Phase 4, not yet)

1. Sign up for a free account at https://universe.roboflow.com and open https://universe.roboflow.com/teamsilver/fightersmma-9vudg
2. Click **Download Dataset**, choose format **YOLOv8** (or YOLOv11), then **Download zip to computer**, or copy the `curl` snippet it shows. That snippet contains your private API key, so don't paste it into any file in this repo.
3. Unzip into `data/raw/fightersmma/`.

## 5. Mendeley MMA Fighter Detection (optional, Phase 4)

Open https://data.mendeley.com/datasets/c456bnk8bm/1, click **Download All**, and unzip into `data/raw/mendeley_mma/`.

## 6. YOLO11-pose weights (optional locally; the notebook fetches them)

```bash
mkdir -p models && curl -L --fail -o models/yolo11s-pose.pt https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s-pose.pt
```

Swap `s` for `n` (fastest) or `m` (more accurate). License: AGPL-3.0 (Ultralytics).

## 7. RTMO ONNX (optional locally; rtmlib fetches it automatically)

```bash
mkdir -p models/rtmo && curl -L --fail -o models/rtmo/rtmo-m.zip https://download.openmmlab.com/mmpose/v1/projects/rtmo/onnx_sdk/rtmo-m_16xb16-600e_body7-640x640-39e78cc4_20231211.zip
```

For RTMO-l use `.../rtmo-l_16xb16-600e_body7-640x640-b37118ce_20231211.zip`. License: Apache-2.0.

## Not recommended

- **YOLO-NAS Pose (super-gradients)**: the reference repo talhaahussain/grappling-pose-identification uses it, but the pretrained weights are under a separate non-commercial license, and the super-gradients project is no longer actively maintained. YOLO11 or RTMO cover the same ground.
