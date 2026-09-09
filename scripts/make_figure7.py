#!/usr/bin/env python
"""
Figure 7 — Networks versus communities.

The Schaefer parcellation ships an a priori functional partition: 17 canonical
networks. The five communities in Figures 1-6 were derived from the structural
data itself. This figure asks whether they agree, and answers no.

  A  the 16 x 16 network x network connectivity matrix, in canonical Yeo order
  B  modularity Q of four candidate partitions on the same connectome
  C  how the five communities distribute across the 16 networks

Panel B is the load-bearing one. A partition is a good description of a network
if its modularity is high, so putting the a priori and data-driven partitions on
one axis says directly which better describes structural connectivity. The
functional networks score below a partition that merely splits the brain in
half, which is the whole finding.

Panel A is deliberately left in canonical order rather than reordered to look
blocky. Figure 2 could reorder because the point there was that blocks exist;
here the point is that they largely do not, and permuting until they appeared
would manufacture the opposite conclusion.

    env/bin/python scripts/make_figure7.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LogNorm
from sklearn.metrics import adjusted_mutual_info_score

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]
BAR = "#2a78d6"

#: Canonical Yeo-17 ordering, with the display abbreviations used in Figure 6.
CANON = [("VisCent", "Vis-C"), ("VisPeri", "Vis-P"),
         ("SomMotA", "SomMot-A"), ("SomMotB", "SomMot-B"),
         ("DorsAttnA", "dAttn-A"), ("DorsAttnB", "dAttn-B"),
         ("SalVentAttnA", "vAttn-A"), ("SalVentAttnB", "vAttn-B"),
         ("Limbic", "Limbic"),
         ("ContA", "Cont-A"), ("ContB", "Cont-B"), ("ContC", "Cont-C"),
         ("TempPar", "TempPar"),
         ("DefaultA", "Def-A"), ("DefaultB", "Def-B"), ("DefaultC", "Def-C")]


def main():
    W = cd.group_average()
    assign = cd.communities()
    names = cd.region_labels()
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)
    n = len(assign)

    net = np.array([m.split("_")[1] for m in names])
    hemi = np.array([m.split("_")[0] for m in names])
    order = [k for k, _ in CANON if (net == k).any()]
    labels = [lab for k, lab in CANON if (net == k).any()]
    N = len(order)

    # network x network mean connectivity
    M = np.zeros((N, N))
    for i, ka in enumerate(order):
        for j, kb in enumerate(order):
            ia, ib = net == ka, net == kb
            block = W[np.ix_(ia, ib)]
            block = (block[np.triu_indices(block.shape[0], 1)] if i == j
                     else block.ravel())
            M[i, j] = block.mean() if block.size else 0.0

    # modularity of each candidate partition on the same graph
    G = nx.from_numpy_array(W)

    def Q(lab):
        parts = [set(np.flatnonzero(lab == u).tolist()) for u in np.unique(lab)]
        return nx.community.modularity(G, parts, weight="weight")

    netid = np.array([order.index(x) for x in net])
    hemid = np.array([0 if h == "LH" else 1 for h in hemi])
    hn = np.array([f"{h}_{x}" for h, x in zip(hemi, net)])
    hnid = np.array([sorted(set(hn)).index(x) for x in hn])
    parts = [(f"Communities ({len(present)})", Q(assign)),
             ("Hemisphere (2)", Q(hemid)),
             (f"Networks ({N})", Q(netid)),
             (f"Networks × hemi ({len(set(hn))})", Q(hnid))]
    ami_net = adjusted_mutual_info_score(assign, netid)
    ami_hemi = adjusted_mutual_info_score(assign, hemid)

    # communities x networks cross-tab
    X = np.zeros((len(present), N), dtype=int)
    for r, k in enumerate(present):
        for c, s in enumerate(order):
            X[r, c] = int(((assign == k) & (net == s)).sum())

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 5.55))
    fig.text(0.035, 0.976, "Networks versus communities", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")
    fig.text(0.035, 0.943,
             "The parcellation's a priori functional networks, set against the "
             "communities derived from the structural data itself.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="top")

    gs = fig.add_gridspec(2, 2, left=0.088, right=0.985, top=0.845,
                          bottom=0.255, wspace=0.42, hspace=0.70,
                          width_ratios=[1.0, 0.92], height_ratios=[1.0, 0.58])

    # ---------- A: network x network ---------------------------------------
    axA = fig.add_subplot(gs[:, 0])
    im = axA.imshow(M, cmap=cs.sequential_cmap(),
                    norm=LogNorm(vmin=max(M[M > 0].min(), 1), vmax=M.max()),
                    interpolation="nearest", aspect="auto")
    axA.set_xticks(range(N)); axA.set_yticks(range(N))
    axA.set_xticklabels(labels, rotation=90, fontsize=5.2)
    axA.set_yticklabels(labels, fontsize=5.2)
    axA.tick_params(length=0, pad=2)
    for s in axA.spines.values():
        s.set_visible(False)
    cax = fig.add_axes([0.088, 0.072, 0.30, 0.013])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2.5, width=0.6, labelsize=cs.TYPE["caption"],
                      color=INK["muted"], labelcolor=INK["secondary"])
    cb.set_label("mean streamline count", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], labelpad=3)

    # ---------- B: modularity ----------------------------------------------
    axB = fig.add_subplot(gs[0, 1])
    ypos = np.arange(len(parts))[::-1]
    axB.barh(ypos, [q for _, q in parts], height=0.62, color=BAR,
             edgecolor=cs.SURFACE[MODE], linewidth=1.0)
    for y, (lab, q) in zip(ypos, parts):
        axB.text(q + 0.012, y, f"{q:.3f}", va="center", ha="left",
                 fontsize=cs.TYPE["caption"], color=INK["primary"],
                 weight="semibold")
    axB.set_yticks(ypos)
    axB.set_yticklabels([lab for lab, _ in parts], fontsize=cs.TYPE["caption"])
    axB.set_xlim(0, 0.63)
    axB.set_xlabel("modularity Q on this connectome", labelpad=2)
    axB.grid(True, axis="x", color=INK["grid"], linewidth=0.5)
    axB.set_axisbelow(True)
    axB.tick_params(axis="y", length=0)

    # ---------- C: cross-tab ------------------------------------------------
    axC = fig.add_subplot(gs[1, 1])
    axC.imshow(X, cmap=cs.sequential_cmap(), interpolation="nearest",
               vmin=0, vmax=X.max(), aspect="auto")
    axC.set_xticks(range(N)); axC.set_xticklabels(labels, rotation=90,
                                                  fontsize=5.2)
    axC.set_yticks(range(len(present)))
    axC.set_yticklabels([str(k + 1) for k in present],
                        fontsize=cs.TYPE["caption"])
    axC.tick_params(length=0, pad=3)
    for s in axC.spines.values():
        s.set_visible(False)
    for r in range(len(present)):
        axC.add_patch(plt.Rectangle((-1.15, r - 0.5), 0.55, 1,
                                    facecolor=cs.community_color(present[r]),
                                    edgecolor="none", clip_on=False))
        for c in range(N):
            if X[r, c]:
                axC.text(c, r, str(X[r, c]), ha="center", va="center",
                         fontsize=4.8,
                         color=cs.SURFACE[MODE] if X[r, c] > X.max() * 0.55
                         else INK["primary"])
    axC.set_ylabel("community", labelpad=12)

    for ax, head, sub in (
            (axA, "A   Network × network connectivity",
             "canonical Yeo order, not reordered"),
            (axB, "B   Which partition describes the structure?",
             "higher Q = better structural description"),
            (axC, "C   Communities across networks",
             f"regions in common · AMI {ami_net:.2f}")):
        pos = ax.get_position()
        fig.text(pos.x0, pos.y1 + 0.052, head,
                 fontsize=cs.TYPE["panel_title"], weight="semibold",
                 color=INK["primary"], va="baseline")
        fig.text(pos.x0, pos.y1 + 0.018, sub, fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], va="baseline")

    fig.text(0.505, 0.020,
             "The a priori functional networks describe this connectome\n"
             "worse than splitting the brain in half, and the two partitions\n"
             f"barely agree (AMI {ami_net:.2f} with networks, {ami_hemi:.2f} "
             "with hemisphere).\nStructural modules here follow space, not "
             "function.",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom",
             linespacing=1.55)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure7_networks_vs_communities.pdf"))
    fig.savefig(os.path.join(OUT, "figure7_networks_vs_communities.png"),
                dpi=400)
    plt.close(fig)
    for lab, q in parts:
        print(f"  Q  {lab:34s} {q:.3f}")
    print(f"  AMI communities~networks   : {ami_net:.3f}")
    print(f"  AMI communities~hemisphere : {ami_hemi:.3f}")
    print("  wrote figures/figure7_networks_vs_communities.{pdf,png}")


if __name__ == "__main__":
    main()
