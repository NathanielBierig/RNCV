"""Grid-overlaid clean eval frames for by-eye role ground truth (roles_gt.csv).
Grid: 12 columns A-L x 8 rows 1-8 over the full frame; a cell like 'F4' means its centre.
    python -I research/pose_review/gt_sheets.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, load_cache  # noqa: E402

NC, NR, W = 12, 8, 640


def gridded(img):
    h = int(img.shape[0] * W / img.shape[1])
    im = cv2.resize(img, (W, h))
    for c in range(1, NC):
        x = int(c * W / NC)
        cv2.line(im, (x, 0), (x, h), (0, 255, 255), 1)
    for r in range(1, NR):
        y = int(r * h / NR)
        cv2.line(im, (0, y), (W, y), (0, 255, 255), 1)
    for c in range(NC):
        cv2.putText(im, "ABCDEFGHIJKL"[c], (int((c + .4) * W / NC), 12), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 255, 255), 1)
    for r in range(NR):
        cv2.putText(im, str(r + 1), (2, int((r + .6) * h / NR)), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 255, 255), 1)
    return im


def main():
    cache = load_cache()
    tiles = []
    for e in cache:
        im = gridded(cv2.imread(str(OUT / "frames" / f"r{e['row']:02d}_{e['pos']}.jpg")))
        im = cv2.copyMakeBorder(im, 22, 0, 0, 0, cv2.BORDER_CONSTANT)
        cv2.putText(im, f"row {e['row']} {e['pos']}  attacker_side={e['attacker_side']}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
        tiles.append(cv2.resize(im, (W, 22 + 360)))
    (OUT / "gt").mkdir(exist_ok=True)
    for s in range(0, len(tiles), 6):
        t = tiles[s:s + 6] + [np.zeros_like(tiles[0])] * (6 - len(tiles[s:s + 6]))
        sheet = np.vstack([np.hstack(t[i:i + 2]) for i in range(0, 6, 2)])
        cv2.imwrite(str(OUT / "gt" / f"gt{s // 6 + 1}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    main()
