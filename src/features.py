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


N_ATH = 62            # per-athlete block in build(): 17*3 coords/conf + 8 angles + 3 torso
N_K = len(KEY_JOINTS)


def build_role_invariant(poses):
    """Features identical under pose1 <-> pose2 swap (critique #13).

    Athletes are put in a canonical order, "top" first (hip centre higher in the
    image; a missing athlete goes second), and pair features are symmetrized.
    Returns (X, names, a1_is_top): a1_is_top says which original athlete came
    first, so identity-tied labels (mount1/mount2) can be mapped to and from
    canonical "suffix athlete is top / bottom" labels.
    """
    X, _ = build(poses)
    a1, a2 = X[:, :N_ATH], X[:, N_ATH:2 * N_ATH]
    hip_dx, hip_dy, hip_dist = X[:, 2 * N_ATH], X[:, 2 * N_ATH + 1], X[:, 2 * N_ATH + 2]
    D = X[:, 2 * N_ATH + 3: 2 * N_ATH + 3 + N_K * N_K].reshape(-1, N_K, N_K)   # a1 joint i vs a2 joint j
    miss = X[:, -2:]
    # hip_dy = y(a1) - y(a2); image y grows downward, so a1 is top when hip_dy < 0
    a1_is_top = np.where(np.isnan(hip_dy), miss[:, 1] == 1, hip_dy < 0)

    top = np.where(a1_is_top[:, None], a1, a2)
    bot = np.where(a1_is_top[:, None], a2, a1)
    Dc = np.where(a1_is_top[:, None, None], D, D.transpose(0, 2, 1))              # rows = top athlete
    iu, iu1 = np.triu_indices(N_K), np.triu_indices(N_K, 1)
    sym = ((D + D.transpose(0, 2, 1)) / 2)[:, iu[0], iu[1]]
    asym = np.abs(D - D.transpose(0, 2, 1))[:, iu1[0], iu1[1]]
    cols = [top, bot, Dc.reshape(len(X), -1), sym, asym,
            np.where(a1_is_top, hip_dx, -hip_dx)[:, None], np.abs(hip_dy)[:, None], hip_dist[:, None],
            np.fmin(a1, a2), np.fmax(a1, a2), miss.sum(1, keepdims=True)]
    kn = list(KEY_JOINTS)
    names = ([f"top_{i}" for i in range(N_ATH)] + [f"bot_{i}" for i in range(N_ATH)] +
             [f"d_top{kn[i]}_bot{kn[j]}" for i in range(N_K) for j in range(N_K)] +
             [f"dsym_{kn[i]}_{kn[j]}" for i, j in zip(*iu)] + [f"dasym_{kn[i]}_{kn[j]}" for i, j in zip(*iu1)] +
             ["hip_dx_top_minus_bot", "hip_dy_abs", "hip_dist"] +
             [f"min_{i}" for i in range(N_ATH)] + [f"max_{i}" for i in range(N_ATH)] + ["n_missing"])
    return np.concatenate(cols, axis=1).astype(np.float32), names, a1_is_top
