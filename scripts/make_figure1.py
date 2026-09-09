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
from matplotlib.lines import Line2D

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402
import figviz                           # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

EDGE_PCT = 97.0        # keep the top 3% of edges
VIEWS = [("l", "Left sagittal"), ("r", "Right sagittal"),
         ("y", "Coronal"), ("z", "Axial")]


def draw_view(ax, direction, W, coords, assign, keep, strength):
    """One glass-brain panel with edges then nodes on top.

    Sagittal views are restricted to their own hemisphere. Projecting both
    hemispheres onto one sagittal plane would superimpose two different
    communities and make the left and right panels look nearly identical,
    hiding the hemispheric split that is the dominant structure here.
    """
    pax = figviz.glass_panel(ax, direction, alpha=0.10)
    P = figviz.project(coords, direction)
    show = figviz.hemisphere_mask(coords, direction)
    figviz.draw_edges(pax, P, keep, assign, show=show,
                      within_lw=0.85, between_lw=0.45, within_alpha=0.55)
    figviz.draw_nodes(pax, P, assign, strength, show=show, mode=MODE, ring=0.7)
    return pax


def main():
    W = cd.group_average()
    assign = cd.communities()
    coords = cd.coordinates()
    Q = cd.modularity()
    sizes = cd.community_sizes(assign)
    present = cd.present_communities(assign)

    # selective edge display
    keep, _, n_edges, n_total = figviz.top_edges(W, EDGE_PCT)
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
    print(f"  edges shown : {n_edges} of {n_total} "
          f"({n_edges / n_total:.1%}), {n_within} within-community")
    print(f"  modularity Q: {Q:.3f}")
    print("  wrote figures/figure1_modular_connectome.{pdf,png}")


if __name__ == "__main__":
    main()
