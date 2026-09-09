#!/usr/bin/env python
"""
Figure 8 — The functional networks.

Where the 16 Schaefer networks sit on the brain, and how they connect.

  A  one small brain per network: its regions in colour against the rest of the
     cortex in grey, in canonical Yeo order so families sit together
  B  the networks as a graph in anatomical space -- each network a node at its
     own centroid, edges weighted by mean between-network connectivity

A note on colour, because it drove the layout. Sixteen categories cannot be
given sixteen colourblind-safe colours; the palette caps identity at six, and no
ordering of more than that clears the all-pairs gate. So the networks are
FACETED rather than colour-coded: one network per panel means no two network
colours are ever compared against each other, and the panel label carries
identity instead. Every panel therefore uses the same single accent, and family
structure (Vis, SomMot, dAttn, vAttn, Limbic, Cont, TempPar, Default) is carried
by reading order rather than by hue.

Panel B is the one place networks appear together. It resolves the same problem
by not colouring them at all: nodes are neutral and labelled directly, with the
data in edge width.

Panel B is laid out on a circle rather than anatomically, which was not the
first attempt. Network centroids average over both hemispheres, so every
bilateral network lands near the midline and an axial view stacks them into an
unreadable column. Panel A already carries the anatomy; freeing panel B from it
lets position serve legibility instead.

    env/bin/python scripts/make_figure8.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402
import figviz                           # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

#: Neutral emphasis, deliberately not one of the six community slots -- these
#: panels are about networks, and reusing a community colour would imply an
#: identity that is not being claimed.
ACCENT = "#184f95"

CANON = [("VisCent", "Vis-C"), ("VisPeri", "Vis-P"),
         ("SomMotA", "SomMot-A"), ("SomMotB", "SomMot-B"),
         ("DorsAttnA", "dAttn-A"), ("DorsAttnB", "dAttn-B"),
         ("SalVentAttnA", "vAttn-A"), ("SalVentAttnB", "vAttn-B"),
         ("Limbic", "Limbic"), ("ContA", "Cont-A"), ("ContB", "Cont-B"),
         ("ContC", "Cont-C"), ("TempPar", "TempPar"),
         ("DefaultA", "Def-A"), ("DefaultB", "Def-B"), ("DefaultC", "Def-C")]

N_NET_EDGES = 26


def main():
    W = cd.group_average()
    names = cd.region_labels()
    coords = cd.coordinates()
    net = np.array([m.split("_")[1] for m in names])

    order = [k for k, _ in CANON if (net == k).any()]
    labels = {k: lab for k, lab in CANON}
    N = len(order)
    counts = {k: int((net == k).sum()) for k in order}

    # network x network mean connectivity
    M = np.zeros((N, N))
    for i, ka in enumerate(order):
        for j, kb in enumerate(order):
            ia, ib = net == ka, net == kb
            blk = W[np.ix_(ia, ib)]
            blk = (blk[np.triu_indices(blk.shape[0], 1)] if i == j
                   else blk.ravel())
            M[i, j] = blk.mean() if blk.size else 0.0

    deg = W.sum(1)
    node_s = 7 + 22 * (deg - deg.min()) / (deg.max() - deg.min())

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 8.55))
    fig.text(0.035, 0.980, "The functional networks", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")
    fig.text(0.035, 0.958,
             "The 16 Schaefer networks present in the 100-region atlas: where "
             "each sits on the cortex, and how they interconnect.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="top")

    # ---------- A: 4 x 4 facet grid ----------------------------------------
    fig.text(0.035, 0.928, "A   Each network on the cortex",
             fontsize=cs.TYPE["panel_title"], weight="semibold",
             color=INK["primary"], va="baseline")
    fig.text(0.035, 0.910,
             "canonical Yeo order; regions of one network in colour against "
             "the rest of the cortex in grey",
             fontsize=cs.TYPE["caption"], color=INK["secondary"], va="baseline")

    gsA = fig.add_gridspec(4, 4, left=0.030, right=0.970, top=0.888,
                           bottom=0.360, hspace=0.30, wspace=0.02)
    for idx, k in enumerate(order):
        ax = fig.add_subplot(gsA[idx // 4, idx % 4])
        pax = figviz.glass_panel(ax, "z", alpha=0.085)
        P = figviz.project(coords, "z")
        sel = net == k
        figviz.draw_nodes(pax, P, np.zeros(len(P), int), node_s * 0.5,
                          show=~sel, mode=MODE, ring=0.0, zorder=2,
                          color_override=cs.CONTEXT_NODE)
        figviz.draw_nodes(pax, P, np.zeros(len(P), int), node_s, show=sel,
                          mode=MODE, ring=0.6, zorder=4,
                          color_override=ACCENT)
        ax.set_title(f"{labels[k]}   {counts[k]}",
                     fontsize=cs.TYPE["caption"], color=INK["primary"],
                     loc="center", pad=1.5)

    # ---------- B: networks as a circular graph ----------------------------
    fig.text(0.035, 0.324, "B   Connectivity between networks",
             fontsize=cs.TYPE["panel_title"], weight="semibold",
             color=INK["primary"], va="baseline")
    fig.text(0.035, 0.306,
             f"the {N_NET_EDGES} strongest between-network connections, "
             "chord width by mean streamline count; node size by regions",
             fontsize=cs.TYPE["caption"], color=INK["secondary"], va="baseline")

    iu = np.triu_indices(N, 1)
    strengths = M[iu]
    keep = np.argsort(strengths)[::-1][:N_NET_EDGES]
    wmax = strengths.max()

    axB = fig.add_axes([0.30, 0.080, 0.40, 0.196])
    axB.set_aspect("equal"); axB.set_axis_off()
    axB.set_xlim(-1.75, 1.75); axB.set_ylim(-1.30, 1.30)

    ang = np.linspace(90, 90 - 360, N, endpoint=False)
    pts = np.array([[np.cos(np.radians(a)), np.sin(np.radians(a))]
                    for a in ang])

    for e in keep:
        i, j = iu[0][e], iu[1][e]
        p1, p2 = pts[i], pts[j]
        sep = np.arccos(np.clip(np.dot(p1, p2), -1, 1))
        k = 0.45 * (1 - 0.55 * (1 - sep / np.pi))
        path = Path([p1, p1 * k, p2 * k, p2],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
        axB.add_patch(PathPatch(
            path, facecolor="none", edgecolor=cs.CONTEXT_EDGE,
            linewidth=0.4 + 3.0 * (strengths[e] / wmax) ** 0.7,
            zorder=2, capstyle="round"))

    sizes = np.array([counts[k] for k in order], dtype=float)
    axB.scatter(pts[:, 0], pts[:, 1], s=14 + 7 * sizes, c=ACCENT,
                edgecolors=cs.SURFACE[MODE], linewidths=1.0, zorder=4)
    for i, k in enumerate(order):
        a = ang[i]
        lp = pts[i] * 1.13
        rot = a if -90 <= a <= 90 else a + 180
        ha = "left" if -90 <= a <= 90 else "right"
        axB.text(lp[0], lp[1], labels[k], rotation=rot,
                 rotation_mode="anchor", ha=ha, va="center",
                 fontsize=cs.TYPE["caption"], color=INK["secondary"],
                 zorder=5)

    top = [(labels[order[iu[0][e]]], labels[order[iu[1][e]]], strengths[e])
           for e in keep[:3]]
    fig.text(0.035, 0.032,
             "strongest pairs:  " + " · ".join(f"{a}–{b} {v:,.0f}"
                                               for a, b, v in top),
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")
    fig.text(0.035, 0.013,
             "Sixteen categories cannot be given sixteen colourblind-safe "
             "colours, so networks are faceted in A and left uncoloured in B.",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure8_functional_networks.pdf"))
    fig.savefig(os.path.join(OUT, "figure8_functional_networks.png"), dpi=400)
    plt.close(fig)
    print(f"  {N} networks, sizes {counts}")
    print("  strongest between-network pairs:")
    for a, b, v in top:
        print(f"    {a}–{b}: {v:,.0f}")
    print("  wrote figures/figure8_functional_networks.{pdf,png}")


if __name__ == "__main__":
    main()
