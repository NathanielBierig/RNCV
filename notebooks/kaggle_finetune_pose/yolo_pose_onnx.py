"""Run a YOLO-pose ONNX file (e.g. the Kaggle fine-tune output) with onnxruntime only.

Drop-in for rtmlib's RTMO in src/pose_smoke.py:
    model = YoloPoseOnnx("models/rncv_pose_v1.onnx")
    kps, scores = model(frame_bgr, nms_thr=0.65, score_thr=0.25)
    # kps [N, 17, 2] pixel coords (COCO-17 order), scores [N, 17] keypoint confidences
model.last_boxes / model.last_box_scores hold the person boxes [N, 4] (x1, y1, x2, y2) and scores [N].

Needs only numpy, opencv and onnxruntime (no torch, no ultralytics), so it runs on the laptop CPU.
The ONNX output is [1, 5 + 17*3, anchors]: cx, cy, w, h, person score, then x, y, conf per joint.
"""
import cv2
import numpy as np
import onnxruntime as ort


class YoloPoseOnnx:
    def __init__(self, onnx_path, device="cpu"):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if device == "cuda" else ["CPUExecutionProvider"]
        self.sess = ort.InferenceSession(str(onnx_path), providers=providers)
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        h, w = inp.shape[2], inp.shape[3]
        self.size = (int(h) if isinstance(h, int) else 640, int(w) if isinstance(w, int) else 640)
        self.last_boxes = np.zeros((0, 4), np.float32)
        self.last_box_scores = np.zeros((0,), np.float32)

    def _letterbox(self, img):
        """Resize keeping aspect ratio and pad with grey 114 (same as Ultralytics)."""
        H, W = self.size
        h, w = img.shape[:2]
        r = min(H / h, W / w)
        nh, nw = int(round(h * r)), int(round(w * r))
        top, left = int(round((H - nh) / 2 - 0.1)), int(round((W - nw) / 2 - 0.1))
        out = np.full((H, W, 3), 114, np.uint8)
        out[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        return out, r, left, top

    def __call__(self, image, nms_thr=0.65, score_thr=0.25):
        lb, r, dx, dy = self._letterbox(image)
        x = lb[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        pred = self.sess.run(None, {self.input_name: np.ascontiguousarray(x)})[0][0]  # [56, A]
        pred = pred.T                                                                 # [A, 56]
        pred = pred[pred[:, 4] >= score_thr]
        if len(pred) == 0:
            self.last_boxes = np.zeros((0, 4), np.float32)
            self.last_box_scores = np.zeros((0,), np.float32)
            return np.zeros((0, 17, 2), np.float32), np.zeros((0, 17), np.float32)
        cx, cy, bw, bh = pred[:, 0], pred[:, 1], pred[:, 2], pred[:, 3]
        xywh = np.stack([cx - bw / 2, cy - bh / 2, bw, bh], 1)
        keep = cv2.dnn.NMSBoxes(xywh.tolist(), pred[:, 4].tolist(), score_thr, nms_thr)
        keep = np.array(keep, dtype=int).reshape(-1)
        keep = keep[np.argsort(-pred[keep, 4])]
        pred, xywh = pred[keep], xywh[keep]
        kpts = pred[:, 5:].reshape(-1, 17, 3).copy()
        kpts[..., 0] = (kpts[..., 0] - dx) / r
        kpts[..., 1] = (kpts[..., 1] - dy) / r
        boxes = np.stack([(xywh[:, 0] - dx) / r, (xywh[:, 1] - dy) / r,
                          (xywh[:, 0] + xywh[:, 2] - dx) / r, (xywh[:, 1] + xywh[:, 3] - dy) / r], 1)
        self.last_boxes = boxes.astype(np.float32)
        self.last_box_scores = pred[:, 4].astype(np.float32)
        return kpts[..., :2].astype(np.float32), kpts[..., 2].astype(np.float32)
