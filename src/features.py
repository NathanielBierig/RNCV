"""Turn raw 2-athlete COCO keypoints into a per-frame feature vector.

Normalization: both athletes are expressed in one shared frame, centred on the
midpoint of their hip centres and scaled by the diagonal of the box around all
joints. That removes camera position and zoom but keeps who is above whom.
Missing athletes / low-confidence joints become NaN (the booster handles NaN).
"""
import numpy as np

# COCO-17 indices
NOSE, L_SH, R_SH, L_EL, R_EL, L_WR, R_WR = 0, 5, 6, 7, 8, 9, 10
L_HIP, R_HIP, L_KN, R_KN, L_AN, R_AN = 11, 12, 13, 14, 15, 16
ANGLES = {  # (a, b, c): angle at b
    "l_elbow": (L_SH, L_EL, L_WR), "r_elbow": (R_SH, R_EL, R_WR),
    "l_knee": (L_HIP, L_KN, L_AN), "r_knee": (R_HIP, R_KN, R_AN),
    "l_shoulder": (L_EL, L_SH, L_HIP), "r_shoulder": (R_EL, R_SH, R_HIP),
    "l_hip": (L_SH, L_HIP, L_KN), "r_hip": (R_SH, R_HIP, R_KN),
}
KEY_JOINTS = {"nose": NOSE, "l_wr": L_WR, "r_wr": R_WR, "l_hip": L_HIP,
              "r_hip": R_HIP, "l_an": L_AN, "r_an": R_AN}
CONF_MIN = 0.2


def _angle(a, b, c):
    v1, v2 = a - b, c - b
    cos = (v1 * v2).sum(-1) / (np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def build(poses):
    """poses: [N, 2, 17, 3] -> (X [N, F] float32, feature names)."""
    xy = poses[..., :2].copy()
    conf = poses[..., 2]
    xy[conf < CONF_MIN] = np.nan

    hip_c = np.nanmean(xy[:, :, [L_HIP, R_HIP]], axis=2)            # [N, 2, 2]
    body_c = np.nanmean(xy, axis=2)
    hip_c = np.where(np.isnan(hip_c), body_c, hip_c)                # fall back to body centre
    centre = np.nanmean(hip_c, axis=1)                              # [N, 2]
    flat = xy.reshape(len(xy), -1, 2)
    span = np.nanmax(flat, axis=1) - np.nanmin(flat, axis=1)
    scale = np.linalg.norm(span, axis=1)
    scale = np.where(scale > 1, scale, np.nan)
    norm = (xy - centre[:, None, None, :]) / scale[:, None, None, None]

    cols, names = [], []
    for a in range(2):
        tag = f"a{a + 1}"
        for j in range(17):
            for d, axis in enumerate("xy"):
                cols.append(norm[:, a, j, d]); names.append(f"{tag}_j{j}_{axis}")
            cols.append(conf[:, a, j]); names.append(f"{tag}_j{j}_c")
        for nm, (i, k, l) in ANGLES.items():
            cols.append(_angle(xy[:, a, i], xy[:, a, k], xy[:, a, l])); names.append(f"{tag}_ang_{nm}")
        sh = np.nanmean(norm[:, a, [L_SH, R_SH]], axis=1)
        hp = np.nanmean(norm[:, a, [L_HIP, R_HIP]], axis=1)
        torso = sh - hp
        cols.append(np.degrees(np.arctan2(torso[:, 1], torso[:, 0]))); names.append(f"{tag}_torso_dir")
        cols.append(np.linalg.norm(torso, axis=1)); names.append(f"{tag}_torso_len")
        cols.append(np.nanmean(norm[:, a, :, 1], axis=1)); names.append(f"{tag}_mean_y")

    hc = (hip_c - centre[:, None, :]) / scale[:, None, None]
    cols.append(hc[:, 0, 0] - hc[:, 1, 0]); names.append("hip_dx")
    cols.append(hc[:, 0, 1] - hc[:, 1, 1]); names.append("hip_dy")       # + means athlete 1 lower in image
    cols.append(np.linalg.norm(hc[:, 0] - hc[:, 1], axis=1)); names.append("hip_dist")
    for n1, j1 in KEY_JOINTS.items():
        for n2, j2 in KEY_JOINTS.items():
            d = np.linalg.norm(norm[:, 0, j1] - norm[:, 1, j2], axis=1)
            cols.append(d); names.append(f"d_a1{n1}_a2{n2}")
    cols.append(np.isnan(poses[:, 0, 0, 0]).astype(np.float32)); names.append("a1_missing")
    cols.append(np.isnan(poses[:, 1, 0, 0]).astype(np.float32)); names.append("a2_missing")
    X = np.stack(cols, axis=1).astype(np.float32)
    return X, names
