#!/usr/bin/env python
"""
Figure 2 — Communities in connectivity space.

The region x region connectivity matrix, reordered by community.

Two panels, deliberately. Showing only the reordered matrix would beg the
question: any matrix can be made to look blocky if you are free to permute it.
So the atlas-order matrix is shown alongside, on an identical colour scale, and
the two differ only by a permutation of rows and columns. The block structure on
the right is therefore a property of the data, not of the rendering.

Encoding:
  colour      log streamline count (sequential, one hue -- magnitude)
  colour bars community identity along both edges (categorical -- identity)
  boundaries  community blocks

Those are separate channels on purpose: the community palette never encodes
magnitude, and the sequential ramp never encodes identity.

    env/bin/python scripts/make_figure2.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]


def draw_matrix(ax, M, vmax, cmap):
    im = ax.imshow(M, cmap=cmap, interpolation="nearest", vmin=0, vmax=vmax)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def main():
    W = cd.group_average()
    assign = cd.communities()
    names = cd.region_labels()
    n = len(assign)
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)

    shown = np.log1p(W)
    vmax = np.percentile(shown, 99.5)
    cmap = cs.sequential_cmap()

    order, bounds, _ = cs.order_by_community(assign)
    M_comm = shown[np.ix_(order, order)]

    # hemisphere split in the atlas ordering, for the left panel's divider
    hemi = np.array([1 if nm.startswith("RH") else 0 for nm in names])
    split = int(np.argmax(hemi == 1))

    # within vs between, on the raw counts
    same = assign[:, None] == assign[None, :]
    off = ~np.eye(n, dtype=bool)
    within_mean = W[same & off].mean()
    between_mean = W[~same & off].mean()

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 4.7))

    fig.text(0.045, 0.955, "Communities in connectivity space", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")
    fig.text(0.045, 0.905,
             "The same 100 × 100 group-average matrix under two orderings. "
             "Reordering by community is a permutation only — no\nvalue "
             "changes — so the blocks on the right are structure in the data, "
             "not in the rendering.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="top",
             linespacing=1.5)

    gs = fig.add_gridspec(1, 2, left=0.055, right=0.86, top=0.735,
                          bottom=0.115, wspace=0.20)

    # ---- left: atlas order -------------------------------------------------
    ax0 = fig.add_subplot(gs[0])
    draw_matrix(ax0, shown, vmax, cmap)
    ax0.axhline(split - 0.5, color=INK["primary"], lw=0.7, alpha=0.45)
    ax0.axvline(split - 0.5, color=INK["primary"], lw=0.7, alpha=0.45)
    ax0.set_title("Schaefer atlas order", fontsize=cs.TYPE["panel_title"],
                  weight="semibold", color=INK["primary"], loc="left", pad=30)
    ax0.annotate("grouped by hemisphere, then network",
                 xy=(0, 1), xycoords="axes fraction", xytext=(0, 18),
                 textcoords="offset points", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], ha="left", va="bottom")
    for lab, pos in (("LH", split / 2), ("RH", split + (n - split) / 2)):
        ax0.annotate(lab, xy=(-0.035, 1 - pos / n), xycoords="axes fraction",
                     fontsize=cs.TYPE["caption"], color=INK["muted"],
                     ha="right", va="center")

    # ---- right: community order -------------------------------------------
    ax1 = fig.add_subplot(gs[1])
    im = draw_matrix(ax1, M_comm, vmax, cmap)
    cs.community_colorbars(ax1, assign, order, mode=MODE, width=0.030)
    cs.draw_community_blocks(ax1, bounds, n, mode=MODE, lw=0.8)
    ax1.set_title("Community order", fontsize=cs.TYPE["panel_title"],
                  weight="semibold", color=INK["primary"], loc="left", pad=30)
    ax1.annotate("same matrix, rows and columns permuted",
                 xy=(0, 1), xycoords="axes fraction", xytext=(0, 18),
                 textcoords="offset points", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], ha="left", va="bottom")

    # number each diagonal block -- identity never rests on colour alone
    starts = np.r_[0, bounds]
    ends = np.r_[bounds, n]
    for k, (a, b) in zip(present, zip(starts, ends)):
        mid = (a + b) / 2 - 0.5
        ax1.text(mid, mid, str(k + 1), ha="center", va="center",
                 fontsize=cs.TYPE["annotation"], weight="semibold",
                 color=INK["primary"],
                 bbox=dict(boxstyle="circle,pad=0.22", linewidth=0,
                           facecolor=cs.SURFACE[MODE], alpha=0.82))

    # ---- colourbar ---------------------------------------------------------
    cax = fig.add_axes([0.885, 0.115, 0.016, 0.62])
    cb = fig.colorbar(im, cax=cax)
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2.5, width=0.6, labelsize=cs.TYPE["caption"],
                      color=INK["muted"], labelcolor=INK["secondary"])
    cb.set_label("log(1 + streamline count)", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], labelpad=6)

    # ---- legend + summary --------------------------------------------------
    handles = [Line2D([], [], marker="s", linestyle="none", markersize=6,
                      markerfacecolor=cs.community_color(k),
                      markeredgecolor="none",
                      label=f"{k + 1}  ({sizes[k]})") for k in present]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.045, 0.005),
               ncol=len(present), frameon=False, fontsize=cs.TYPE["caption"],
               handletextpad=0.4, columnspacing=1.3,
               title="Community (regions)",
               title_fontsize=cs.TYPE["caption"])
    fig.legends[0].get_title().set_color(INK["muted"])

    fig.text(0.86, 0.018,
             f"within-community mean {within_mean:,.0f}  ·  "
             f"between {between_mean:,.0f}  ·  ratio {within_mean/between_mean:.1f}×",
             fontsize=cs.TYPE["caption"], color=INK["muted"], ha="right",
             va="bottom")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure2_connectivity_space.pdf"))
    fig.savefig(os.path.join(OUT, "figure2_connectivity_space.png"), dpi=400)
    plt.close(fig)
    print(f"  within-community mean : {within_mean:,.1f}")
    print(f"  between-community mean: {between_mean:,.1f}  "
          f"({within_mean/between_mean:.1f}x)")
    print("  wrote figures/figure2_connectivity_space.{pdf,png}")


if __name__ == "__main__":
    main()
