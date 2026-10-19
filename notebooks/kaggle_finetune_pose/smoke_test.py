"""Local CPU check of finetune.ipynb: runs every code cell with a tiny config (RNCV_SMOKE=1).

    C:/Users/netan/.venvs/yolo/Scripts/python.exe notebooks/kaggle_finetune_pose/smoke_test.py <work_dir>
    (add --plan to only list the full Kaggle subset and print its size; no images are fetched)

Fetches ~60 small images (Harmony4D test/16_mma5 + 20 VICOS frames) with HTTP range reads, converts them,
trains yolo11n-pose for 1 epoch at 320 px, evaluates, exports ONNX and checks the wrapper. No UFC footage.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

work = Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "rncv_pose_smoke").resolve()
plan = "--plan" in sys.argv
work.mkdir(parents=True, exist_ok=True)
os.environ.update(RNCV_WORK=str(work / "work"), RNCV_OUT=str(work / "out"),
                  RNCV_VICOS_ANN=str(ROOT / "data" / "raw" / "vicos" / "annotations.json"))
os.environ["RNCV_PLAN_ONLY" if plan else "RNCV_SMOKE"] = "1"
os.environ["MPLBACKEND"] = "Agg"   # no plot windows outside Jupyter
os.chdir(work)   # ultralytics downloads base weights into the working dir

nb = json.loads((HERE / "finetune.ipynb").read_text(encoding="utf-8"))
ns = {"__name__": "__main__"}
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    print(f"\n===== cell {i} =====", flush=True)
    exec(compile(src, f"<cell {i}>", "exec"), ns)
print("\nSMOKE TEST PASSED" if not plan else "\nPLAN DONE")
