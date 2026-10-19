"""Fighter-only boxes for the referee problem (ready to port into src/).

Uses the fight-judge YOLOv8s detector (hasanfaesal/fight-judge-yolov8s, MIT weights,
one class "fighter", trained on 5 k UFC stand-up frames, no referee class), exported
to ONNX so it runs under onnxruntime (no Ultralytics/AGPL code at run time).

    det = FighterDetector("data/referee/detector/weights/fight_judge_yolov8s.onnx")
    boxes, conf = det(frame_bgr)                      # [M, 4] xyxy, [M]
    kpts, scores = gate_people(kpts, scores, boxes)   # RTMO people -> fighters only
    ks, ss, dropped, counts = two_fighters.select(kpts, scores)

gate_people is the "hybrid": keep RTMO's low-threshold people (good on tangled
grappling) but drop anyone who does not overlap a fighter box. If the detector
finds no fighter at all in a frame, nothing is dropped (fall back to RTMO).
"""
import cv2
import numpy as np

THR = 0.3          # joint confidence, same as src/two_fighters.THR


class FighterDetector:
    """YOLOv8 (Ultralytics export, output [1, 4+nc, 8400]) on onnxruntime, CPU."""

    def __init__(self, onnx_path, conf=0.25, iou=0.5, size=640, threads=None):
        import onnxruntime as ort
        so = ort.SessionOptions()
        if threads:
            so.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(str(onnx_path), so, providers=["CPUExecutionProvider"])
        self.inp = self.sess.get_inputs()[0].name
        self.conf, self.iou, self.size = conf, iou, size

    def __call__(self, img):
        h, w = img.shape[:2]
        r = self.size / max(h, w)
        nh, nw = int(round(h * r)), int(round(w * r))
        top, left = (self.size - nh) // 2, (self.size - nw) // 2
        canvas = np.full((self.size, self.size, 3), 114, np.uint8)
        canvas[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        out = self.sess.run(None, {self.inp: np.ascontiguousarray(x)})[0][0]   # [4+nc, N]
        conf = out[4:].max(0)
        m = conf >= self.conf
        if not m.any():
            return np.zeros((0, 4), np.float32), np.zeros(0, np.float32)
        cx, cy, bw, bh = out[:4, m]
        conf = conf[m]
        xywh = np.stack([cx - bw / 2, cy - bh / 2, bw, bh], 1)
        keep = cv2.dnn.NMSBoxes(xywh.tolist(), conf.tolist(), self.conf, self.iou)
        keep = np.array(keep).reshape(-1)
        b = xywh[keep]
        boxes = np.stack([b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]], 1)
        boxes = (boxes - [left, top, left, top]) / r
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, w)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, h)
        return boxes.astype(np.float32), conf[keep].astype(np.float32)


def person_box(k, s, pad=0.1):
    """Box around a person's confident joints (all joints if < 3), padded by `pad`."""
    p = k[s >= THR] if (s >= THR).sum() >= 3 else k
    (x0, y0), (x1, y1) = p.min(0), p.max(0)
    w, h = x1 - x0, y1 - y0
    return np.array([x0 - pad * w, y0 - pad * h, x1 + pad * w, y1 + pad * h])


def iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w * h
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def ioa(a, b):
    """Fraction of box a's area that lies inside box b."""
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area = (a[2] - a[0]) * (a[3] - a[1])
    return w * h / area if area > 0 else 0.0


def gate_people(kpts, scores, fighter_boxes, thr=0.3, mode="iou"):
    """Drop RTMO people that match no fighter box.

    mode "iou": match = IoU >= thr. mode "ioa": match = >= thr of the person's box lies
    inside the fighter box (survives the detector drawing ONE box around two tangled
    fighters, where each fighter's own IoU with it is small).
    kpts [N,17,2], scores [N,17], fighter_boxes [M,4] xyxy.
    Returns (kpts, scores) of the kept people. No fighter boxes -> keep everyone.
    """
    if not len(scores) or not len(fighter_boxes):
        return kpts, scores
    f = iou if mode == "iou" else ioa
    keep = [i for i, (k, s) in enumerate(zip(kpts, scores))
            if max(f(person_box(k, s), fb) for fb in fighter_boxes) >= thr]
    return kpts[keep], scores[keep]


def select_fighters(kpts, scores, fighter_boxes, drop_below=0.2):
    """two_fighters.select with fighter boxes as the referee rule (drop-in replacement).

    1. crowd + duplicate rules exactly as two_fighters.select.
    2. Score each remaining person by fit = the largest fraction of its box that lies inside
       a fighter box (ioa). People with fit < drop_below are dropped (clear outsiders,
       usually the referee) unless that would leave fewer than 2 people.
    3. With 3+ left, keep the 2 with the highest fit (ties -> the old most-overlapping pair).
    No fighter boxes in the frame -> plain two_fighters.select.
    Returns the same tuple as two_fighters.select: (kpts, scores, dropped kpts, counts).
    """
    import two_fighters as tf
    if not len(scores) or not len(fighter_boxes):
        return tf.select(kpts, scores)
    counts = {"crowd": 0, "dup": 0, "ref": 0}
    order = np.argsort(-scores.mean(1))
    kpts, scores = kpts[order], scores[order]
    areas = np.array([tf.box_area(k, s) for k, s in zip(kpts, scores)])
    keep, dropped = [], []
    for i, (k, s) in enumerate(zip(kpts, scores)):
        if areas.max() > 0 and areas[i] < 0.15 * areas.max():
            counts["crowd"] += 1; dropped.append(i); continue
        scale = np.sqrt(max(areas[i], 1.0))
        if any(tf._same_body(k, s, kpts[j], scores[j], scale) for j in keep):
            counts["dup"] += 1; dropped.append(i); continue
        keep.append(i)
    fit = {i: max(ioa(person_box(kpts[i], scores[i]), fb) for fb in fighter_boxes) for i in keep}
    inside = [i for i in keep if fit[i] >= drop_below]
    if len(inside) >= 2 and len(inside) < len(keep):
        out = [i for i in keep if i not in inside]
        counts["ref"] += len(out); dropped += out
        keep = inside
    if len(keep) > 2:
        boxes = {i: tf._box(kpts[i], scores[i]) for i in keep}
        pair_iou = lambda a, b: tf._iou(boxes[a], boxes[b])
        best = max(((a, b) for x, a in enumerate(keep) for b in keep[x + 1:]),
                   key=lambda ab: (round(fit[ab[0]] + fit[ab[1]], 1), pair_iou(*ab), -ab[0] - ab[1]))
        out = [i for i in keep if i not in best]
        counts["ref"] += len(out); dropped += out
        keep = list(best)
    return kpts[keep], scores[keep], [kpts[i] for i in dropped], counts
