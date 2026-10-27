"""README science charts for the current finish model (v0.7c = v0.7 + coach priors).

    python research/model/charts.py

docs/media/effects.png      each factor's odds multiplier with its 80% range (all labels), log scale, x1 = no effect
docs/media/calibration.png  predicted vs observed finish rate at the 2-s landmark, every fight scored by a model
                            that never saw it (leave-one-fight-out), with 95% intervals
"""
import csv
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import model_v07 as m  # noqa: E402
import run_v07_coach as rc  # noqa: E402
import state_model as sm  # noqa: E402

OUT = m.HERE.parents[1] / "docs/media"
INK, MUTED, GRID, ACCENT = "#1f2328", "#656d76", "#d8dee4", "#c4572a"
NAMES = {"arm_under": "Arm under the chin (vs over the jaw)", "flattened": "Defender flattened out",
         "grip_f4": "Figure-four lock (vs one arm)", "grip_other": "Palm / gable / wrist lock (vs one arm)",
         "hand_tucked": "Choking hand hidden", "legs_bt": "Body triangle", "legs_hooks": "Both hooks in",
         "chin_tucked": "Chin tucked", "two_on_one": "Defender 2-on-1 hand fight", "fatigue": "Attacker tired (full)"}


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


def main():
    rc.setup()
    rows = sm.load()
    m.D0.update(m.round_d0(rows))
    cards = list(csv.DictReader(open(m.HERE / "priors_v07.csv", encoding="utf-8")))
    sm.SQUEEZE, sm.CONSCIOUSNESS = sm.SQUEEZE_V06, sm.CONSCIOUSNESS_V06
    sm.USE_FATIGUE = False
    OUT.mkdir(parents=True, exist_ok=True)

    # effects
    beta, cov = rc.fit_cov(rows, cards)
    eff = []
    for n, f in enumerate(m.FEATS):
        if f in NAMES:
            b, se = beta[2 + n], math.sqrt(cov[2 + n, 2 + n])
            eff.append((NAMES[f], math.exp(b), math.exp(b - 1.2816 * se), math.exp(b + 1.2816 * se)))
    eff.sort(key=lambda e: e[1])
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=150)
    ys = np.arange(len(eff))
    for y, (name, mid, lo, hi) in zip(ys, eff):
        ax.plot([lo, hi], [y, y], color=MUTED, lw=2, solid_capstyle="round")
        ax.plot(mid, y, "o", color=ACCENT if mid >= 1 else INK, ms=8, mec="white", mew=1.5)
        ax.text(hi * 1.08, y, f"×{mid:.1f}", va="center", fontsize=9, color=INK)
    ax.axvline(1, color=GRID, lw=1.5, zorder=0)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 4, 8, 16])
    ax.set_xticklabels(["×¼", "×½", "×1", "×2", "×4", "×8", "×16"])
    ax.set_yticks(ys)
    ax.set_yticklabels([e[0] for e in eff], fontsize=9, color=INK)
    style(ax)
    fig.suptitle(f"What moves the odds of a UFC rear-naked choke finishing\n"
                 f"model v0.8 · {len(rows)} labeled attempts · dot = estimate, line = 80% range",
                 fontsize=10, color=INK, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(OUT / "effects.png", facecolor="white")

    # calibration (leave-one-fight-out, landmark prediction)
    preds = m.lofo(rows, cards)
    y = np.array([a for a, _, _, _ in preds])
    p = np.array([b for _, b, _, _ in preds])
    edges = [0, 0.3, 0.5, 0.7, 1.0001]
    fig, ax = plt.subplots(figsize=(4.8, 4.6), dpi=150)
    ax.plot([0, 1], [0, 1], color=GRID, lw=1.5, zorder=0)
    ax.axhline(y.mean(), color=MUTED, lw=1, ls=":", zorder=0)
    ax.text(0.02, y.mean() + 0.02, f"always guess the average ({100 * y.mean():.0f}%)", fontsize=8, color=MUTED)
    for lo, hi in zip(edges, edges[1:]):
        k = (p >= lo) & (p < hi)
        if not k.any():
            continue
        a, b = sm.wilson(int(y[k].sum()), int(k.sum()))
        ax.plot([p[k].mean()] * 2, [a, b], color=MUTED, lw=2, solid_capstyle="round")
        ax.plot(p[k].mean(), y[k].mean(), "o", color=ACCENT, ms=8, mec="white", mew=1.5)
        ax.text(p[k].mean() + 0.02, y[k].mean(), f"n={k.sum()}", fontsize=8, color=MUTED, va="center")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("model said (finish chance at 2 s)", fontsize=9, color=INK)
    ax.set_ylabel("actually finished", fontsize=9, color=INK)
    ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    style(ax)
    ax.spines["left"].set_visible(True); ax.spines["left"].set_color(GRID)
    bl, base = sm.scores(preds)[0], sm.scores(sm.lofo_base(rows))[0]
    ax.set_title(f"Is the finish chance honest?\nheld-out fights · Brier {bl:.3f} (always-the-average {base:.3f})",
                 fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "calibration.png", facecolor="white")
    print("wrote", OUT / "effects.png", OUT / "calibration.png")


if __name__ == "__main__":
    main()
