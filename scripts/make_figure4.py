#!/usr/bin/env python
"""
Figure 4 — Modular brain architecture.

Three panels that build one argument, left to right:

  A  the community x community matrix -- the region-level connectome collapsed
     into within- and between-community summaries
  B  the distributions behind those summaries, because a block mean hides a
     heavily skewed spread
  C  the same comparison held at matched edge length

Panel C exists because of a confound the earlier figures set up. Figure 3
established that these communities are spatially compact, and streamline count
falls off steeply with distance (r = -0.47 here). So "within-community
connectivity is 10x between" risks being a restatement of "within-community
edges are shorter". Binning edges by Euclidean length and comparing like with
like separates the two: if the gap survives inside every bin, modular structure
is not a distance artefact.

On the summary measure. The proposal invites mean, median, proportion of strong
connections, or normalised strength. Measured on these data:

    mean count                 within 430    between 43     10.1x
    median count               within 57     between 0.2   364.5x
    proportion nonzero         within 0.94   between 0.55    1.7x
    proportion > 75th pct      within 0.59   between 0.15    3.9x
    mean log1p count           within 3.94   between 1.21    3.2x

The median is discarded: between-community median is essentially zero, so the
ratio explodes and is an artefact of the denominator, not a finding. The mean is
used in panel A because it is interpretable in streamlines, with a log colour
scale to cope with the range, and panel B shows the spread the mean conceals.

    env/bin/python scripts/make_figure4.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

WITHIN_INK = "#184f95"       # sequential ramp, dark step
BETWEEN_INK = cs.OTHER       # neutral grey
BINS = np.array([0, 30, 50, 70, 90, 200])


def main():
    W = cd.group_average()
    assign = cd.communities()
    coords = cd.coordinates()
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)
    n = len(assign)

    iu = np.triu_indices(n, 1)
    w = W[iu]
    same = assign[iu[0]] == assign[iu[1]]
    dist = np.linalg.norm(coords[iu[0]] - coords[iu[1]], axis=1)

    # community x community mean connectivity
    K = len(present)
    B = np.zeros((K, K))
    for i, ka in enumerate(present):
        for j, kb in enumerate(present):
            ia, ib = assign == ka, assign == kb
            block = W[np.ix_(ia, ib)]
            if ka == kb:
                block = block[np.triu_indices(block.shape[0], 1)]
            B[i, j] = block.mean()

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 3.75))
    fig.text(0.038, 0.965, "Modular brain architecture", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")

    gs = fig.add_gridspec(1, 3, left=0.075, right=0.985, top=0.745,
                          bottom=0.185, wspace=0.42,
                          width_ratios=[1.0, 0.92, 1.12])

    # ---------- A: community x community matrix ----------------------------
    axA = fig.add_subplot(gs[0])
    im = axA.imshow(B, cmap=cs.sequential_cmap(),
                    norm=LogNorm(vmin=max(B.min(), 1), vmax=B.max()),
                    interpolation="nearest")
    axA.set_xticks(range(K)); axA.set_yticks(range(K))
    axA.set_xticklabels([str(k + 1) for k in present])
    axA.set_yticklabels([str(k + 1) for k in present])
    axA.tick_params(length=0, pad=8)
    for s in axA.spines.values():
        s.set_visible(False)
    # community colour on the tick labels' behalf, as small swatches
    for i, k in enumerate(present):
        axA.add_patch(plt.Rectangle((i - 0.5, -0.5 - 0.30), 1, 0.24,
                                    facecolor=cs.community_color(k),
                                    edgecolor="none", clip_on=False))
        axA.add_patch(plt.Rectangle((-0.5 - 0.30, i - 0.5), 0.24, 1,
                                    facecolor=cs.community_color(k),
                                    edgecolor="none", clip_on=False))
    thresh = np.sqrt(B.min() * B.max())
    for i in range(K):
        for j in range(K):
            axA.text(j, i, f"{B[i, j]:,.0f}", ha="center", va="center",
                     fontsize=cs.TYPE["caption"],
                     color=cs.SURFACE[MODE] if B[i, j] > thresh
                     else INK["primary"])

    # ---------- B: distributions -------------------------------------------
    axB = fig.add_subplot(gs[1])
    data, colors, ticks = [], [], []
    for k in present:
        sel = same & (assign[iu[0]] == k)
        data.append(np.log10(w[sel] + 1))
        colors.append(cs.community_color(k))
        ticks.append(str(k + 1))
    data.append(np.log10(w[~same] + 1))
    colors.append(BETWEEN_INK)
    ticks.append("btw")

    parts = axB.violinplot(data, positions=range(len(data)), widths=0.82,
                           showextrema=False, showmedians=True)
    for body, c in zip(parts["bodies"], colors):
        body.set_facecolor(c); body.set_alpha(0.85)
        body.set_edgecolor(cs.SURFACE[MODE]); body.set_linewidth(0.8)
    parts["cmedians"].set_color(INK["primary"])
    parts["cmedians"].set_linewidth(1.1)
    axB.set_xticks(range(len(data)))
    axB.set_xticklabels(ticks)
    axB.set_ylabel("streamline count", labelpad=2)
    axB.set_yticks([0, 1, 2, 3, 4])
    axB.set_yticklabels(["0", "10", "100", "1k", "10k"])
    axB.grid(True, axis="y", color=INK["grid"], linewidth=0.5)
    axB.set_axisbelow(True)

    # ---------- C: distance-matched ----------------------------------------
    axC = fig.add_subplot(gs[2])
    centres, mw, mb, ratio = [], [], [], []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        m = (dist >= lo) & (dist < hi)
        if (m & same).sum() < 5 or (m & ~same).sum() < 5:
            continue
        centres.append((lo + min(hi, 120)) / 2)
        mw.append(w[m & same].mean())
        mb.append(w[m & ~same].mean())
        ratio.append(mw[-1] / mb[-1])
    axC.plot(centres, mw, marker="o", markersize=4.5, color=WITHIN_INK,
             linewidth=2.0, markeredgecolor=cs.SURFACE[MODE],
             markeredgewidth=0.8, zorder=3)
    axC.plot(centres, mb, marker="o", markersize=4.5, color=BETWEEN_INK,
             linewidth=2.0, markeredgecolor=cs.SURFACE[MODE],
             markeredgewidth=0.8, zorder=3)
    axC.set_yscale("log")
    axC.annotate("within", xy=(centres[-1], mw[-1]), xytext=(6, 1),
                 textcoords="offset points", fontsize=cs.TYPE["caption"],
                 color=WITHIN_INK, weight="semibold", va="center")
    axC.annotate("between", xy=(centres[-1], mb[-1]), xytext=(6, 0),
                 textcoords="offset points", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], weight="semibold", va="center")
    for i, (x, r) in enumerate(zip(centres, ratio)):
        axC.annotate(f"{r:.1f}×", xy=(x, np.sqrt(mw[i] * mb[i])),
                     xytext=(6 if i == 0 else 0, 0),
                     textcoords="offset points",
                     ha="center", va="center", fontsize=cs.TYPE["caption"],
                     color=INK["muted"],
                     bbox=dict(boxstyle="round,pad=0.14", linewidth=0,
                               facecolor=cs.SURFACE[MODE], alpha=0.9))
    axC.set_xlabel("edge length (mm)", labelpad=2)
    axC.set_ylabel("mean streamline count", labelpad=2)
    axC.set_xlim(10, 145)
    axC.grid(True, axis="y", color=INK["grid"], linewidth=0.5)
    axC.set_axisbelow(True)

    # Titles as figure text on a shared baseline: panel A's axes are square and
    # therefore shorter than B and C, so axes-anchored titles would step down.
    for ax, head, sub in (
            (axA, "A   Community × community",
             "mean streamline count; diagonal = within"),
            (axB, "B   Edge-weight distributions",
             "per community, plus all between-community"),
            (axC, "C   Held at matched edge length",
             "the gap survives at every length")):
        x0 = ax.get_position().x0
        fig.text(x0, 0.845, head, fontsize=cs.TYPE["panel_title"],
                 weight="semibold", color=INK["primary"], va="baseline")
        fig.text(x0, 0.795, sub, fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], va="baseline")

    fig.text(0.038, 0.030,
             "Within-community edges are shorter than between-community ones "
             "(58 vs 87 mm) and streamline count falls with distance "
             "(r = −0.47), so panel C compares like with like.",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure4_modular_architecture.pdf"))
    fig.savefig(os.path.join(OUT, "figure4_modular_architecture.png"), dpi=400)
    plt.close(fig)
    print("  block means (mean streamline count):")
    for i, k in enumerate(present):
        print("   ", " ".join(f"{v:8.1f}" for v in B[i]))
    print(f"  distance-matched ratios: "
          f"{', '.join(f'{r:.1f}x' for r in ratio)}")
    print("  wrote figures/figure4_modular_architecture.{pdf,png}")


if __name__ == "__main__":
    main()
