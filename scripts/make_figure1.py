#!/usr/bin/env python
"""
Figure 1 — The modular connectome.

A whole-brain network in anatomical space, regions coloured by community.

Design decisions worth knowing:

* SELECTIVE EDGES. Drawing all 4 950 edges is unreadable spaghetti, so only the
  strongest EDGE_PCT of edges are shown. Within-community edges take their
  community's colour; between-community edges are muted grey. Modularity then
  reads directly off the picture: dense colour inside modules, sparse grey
  between them.
* NODE SIZE = weighted degree (strength), so the figure carries magnitude
  without spending the colour channel, which is reserved for identity.
* FOUR VIEWS. Left and right sagittal are shown separately because these
  communities split strongly by hemisphere -- a single view would hide it.
* Communities come from calm_data, never re-detected here, so slot k is the
  same community and colour in every figure.

    env/bin/python scripts/make_figure1.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from nilearn import plotting

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

EDGE_PCT = 97.0        # keep the top 3% of edges
VIEWS = [("l", "Left sagittal"), ("r", "Right sagittal"),
         ("y", "Coronal"), ("z", "Axial")]


def project(coords, direction):
    """MNI mm -> the 2-D plane nilearn draws for each view."""
    x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
    if direction in ("l", "r"):
        return np.c_[y, z]        # sagittal
    if direction == "y":
        return np.c_[x, z]        # coronal
    if direction == "z":
        return np.c_[x, y]        # axial
    raise ValueError(direction)


def draw_view(ax, direction, W, coords, assign, keep, strength):
    """One glass-brain panel with edges then nodes on top.

    Sagittal views are restricted to their own hemisphere. Projecting both
    hemispheres onto one sagittal plane would superimpose two different
    communities and make the left and right panels look nearly identical,
    hiding the hemispheric split that is the dominant structure here.
    """
    display = plotting.plot_glass_brain(
        None, display_mode=direction, axes=ax, annotate=False,
        black_bg=False, alpha=0.10)
    pax = display.axes[direction].ax
    P = project(coords, direction)

    # hemisphere mask for the sagittal panels
    if direction == "l":
        show = coords[:, 0] < 0
    elif direction == "r":
        show = coords[:, 0] >= 0
    else:
        show = np.ones(len(coords), dtype=bool)

    # --- edges: between-community first (recessive), then within (on top) ---
    within, between, wcol = [], [], []
    for i, j in zip(*keep):
        if not (show[i] and show[j]):
            continue
        seg = [P[i], P[j]]
        if assign[i] == assign[j]:
            within.append(seg)
            wcol.append(cs.community_color(int(assign[i])))
        else:
            between.append(seg)

    if between:
        pax.add_collection(LineCollection(
            between, colors=cs.CONTEXT_EDGE, linewidths=0.45, alpha=0.85,
            zorder=2, capstyle="round"))
    if within:
        pax.add_collection(LineCollection(
            within, colors=wcol, linewidths=0.85, alpha=0.55, zorder=3,
            capstyle="round"))

    # --- nodes: size = strength, colour = community, surface ring on top ---
    idx = np.flatnonzero(show)
    idx = idx[np.argsort(strength[idx])]   # weakest first so hubs sit on top
    pax.scatter(P[idx, 0], P[idx, 1],
                s=strength[idx], c=[cs.community_color(int(assign[i]))
                                    for i in idx],
                edgecolors=cs.SURFACE[MODE], linewidths=0.7, zorder=4)
    return pax


def main():
    W = cd.group_average()
    assign = cd.communities()
    coords = cd.coordinates()
    Q = cd.modularity()
    sizes = cd.community_sizes(assign)
    present = cd.present_communities(assign)

    # selective edge display
    iu = np.triu_indices_from(W, 1)
    thr = np.percentile(W[iu], EDGE_PCT)
    keep_mask = W[iu] >= thr
    keep = (iu[0][keep_mask], iu[1][keep_mask])
    n_edges = int(keep_mask.sum())
    n_within = int((assign[keep[0]] == assign[keep[1]]).sum())

    # node size from weighted degree
    deg = W.sum(1)
    strength = 12 + 46 * (deg - deg.min()) / (deg.max() - deg.min())

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 7.4))     # 180 mm wide

    fig.text(0.045, 0.962, "The modular connectome", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")
    fig.text(0.045, 0.928,
             "Group-average CALM 800 structural connectome (n = 315), "
             "Schaefer 100×17. Regions coloured by community;\n"
             "node size is weighted degree. Strongest 3% of connections shown "
             "— within-community in colour, between-community in grey.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="top",
             linespacing=1.5)

    gs = fig.add_gridspec(2, 2, left=0.030, right=0.970, top=0.845,
                          bottom=0.130, hspace=0.05, wspace=0.02,
                          height_ratios=[1.0, 1.45])
    for k, (direction, name) in enumerate(VIEWS):
        ax = fig.add_subplot(gs[k // 2, k % 2])
        draw_view(ax, direction, W, coords, assign, keep, strength)
        ax.set_title(name, fontsize=cs.TYPE["caption"], color=INK["muted"],
                     loc="left", pad=2)

    # legend: identity never rests on colour alone
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=6,
                      markerfacecolor=cs.community_color(k),
                      markeredgecolor=cs.SURFACE[MODE], markeredgewidth=0.8,
                      label=f"Community {k + 1}  ({sizes[k]} regions)")
               for k in present]
    fig.legend(handles=handles, loc="lower left",
               bbox_to_anchor=(0.045, 0.040), ncol=3, frameon=False,
               fontsize=cs.TYPE["caption"], handletextpad=0.5,
               columnspacing=1.6, labelspacing=0.5)

    fig.text(0.970, 0.040,
             f"modularity Q = {Q:.2f}\n{n_within} of {n_edges} shown edges "
             f"are within-community",
             fontsize=cs.TYPE["caption"], color=INK["muted"], ha="right",
             va="bottom", linespacing=1.6)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure1_modular_connectome.pdf"))
    fig.savefig(os.path.join(OUT, "figure1_modular_connectome.png"), dpi=400)
    plt.close(fig)
    print(f"  edges shown : {n_edges} of {len(iu[0])} "
          f"({n_edges / len(iu[0]):.1%}), {n_within} within-community")
    print(f"  modularity Q: {Q:.3f}")
    print("  wrote figures/figure1_modular_connectome.{pdf,png}")


if __name__ == "__main__":
    main()
