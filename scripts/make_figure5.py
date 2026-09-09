#!/usr/bin/env python
"""
Figure 5 — The connectome collapsed.

A morph, in four frames, from the region-level connectome in anatomical space
to the community-level network. Every frame is the same data; only the geometry
changes.

The mechanism: each region's position is linearly interpolated from its true
MNI coordinate toward its own community's centroid,

    pos(t) = (1 - t) * anatomical + t * community centroid

so at t = 0 the panel is Figure 1 and at t = 1 every region of a community sits
at one point and the connectome IS the community graph. Three things are tied
to t so the transformation reads as a single motion rather than four unrelated
pictures:

  * the glass-brain outline fades out, because after t = 0 the positions are no
    longer anatomical and an anatomical frame would be a lie
  * within-community edges fade out, since a collapsing community swallows its
    own internal connections
  * between-community edges keep their endpoints and therefore pile up on the
    same segment, so the super-edges of the final panel assemble themselves out
    of the region-level edges by superposition -- the figure shows where
    community-level connectivity comes from, rather than asserting it

    env/bin/python scripts/make_figure5.py
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

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402
import figviz                           # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

VIEW = "z"          # axial: the hemispheric split is the story here
EDGE_PCT = 96.0
STAGES = [
    (0.00, "Regions", "in anatomical space"),
    (0.45, "Converging", "drawn toward their community"),
    (0.80, "Nearly collapsed", "communities emerging"),
    (1.00, "Communities", "5 super-nodes"),
]


def main():
    W = cd.group_average()
    assign = cd.communities()
    coords = cd.coordinates()
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)
    K = len(present)

    P0 = figviz.project(coords, VIEW)
    cent = {k: P0[assign == k].mean(0) for k in present}
    target = np.array([cent[int(k)] for k in assign])

    pairs, _, n_kept, n_tot = figviz.top_edges(W, EDGE_PCT)
    i_idx, j_idx = pairs
    same = assign[i_idx] == assign[j_idx]

    deg = W.sum(1)
    node_s = 8 + 30 * (deg - deg.min()) / (deg.max() - deg.min())

    # community x community mean connectivity, for the final panel's edges
    B = np.zeros((K, K))
    for a, ka in enumerate(present):
        for b, kb in enumerate(present):
            if a == b:
                continue
            B[a, b] = W[np.ix_(assign == ka, assign == kb)].mean()
    bmax = B.max()

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 3.35))
    fig.text(0.030, 0.965, "The connectome collapsed", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")

    gs = fig.add_gridspec(1, len(STAGES), left=0.022, right=0.978, top=0.760,
                          bottom=0.155, wspace=0.035)

    # Super-node radius is set from the geometry, not by taste: the closest
    # two centroids are ~24 mm apart in this plane, so radii must stay under
    # about 40% of that or the final panel becomes overlapping discs. Area is
    # kept proportional to region count within that ceiling.
    seps = [np.linalg.norm(cent[a] - cent[b])
            for i, a in enumerate(present) for b in present[i + 1:]]
    r_max = 0.40 * min(seps)
    n_max = max(sizes[k] for k in present)
    radius = {k: r_max * np.sqrt(sizes[k] / n_max) for k in present}

    for col, (t, head, sub) in enumerate(STAGES):
        ax = fig.add_subplot(gs[col])
        # the outline fades but still fixes identical axis limits across
        # panels, without which the morph would not read as one motion
        pax = figviz.glass_panel(ax, VIEW, alpha=max(0.004, 0.10 * (1 - t)))
        P = (1 - t) * P0 + t * target

        # between-community edges keep their endpoints, so as the communities
        # converge these pile onto the same segments -- the super-edges of the
        # last panel assemble themselves rather than being asserted
        seg_b = [[P[i], P[j]] for i, j in zip(i_idx[~same], j_idx[~same])]
        if seg_b and t < 1.0:
            pax.add_collection(LineCollection(
                seg_b, colors=cs.CONTEXT_EDGE, linewidths=0.5 + 0.8 * t,
                alpha=0.55 + 0.3 * t, zorder=2, capstyle="round"))

        # within-community edges are swallowed by the collapsing community
        if t < 1.0:
            seg_w = [[P[i], P[j]] for i, j in zip(i_idx[same], j_idx[same])]
            col_w = [cs.community_color(int(assign[i])) for i in i_idx[same]]
            pax.add_collection(LineCollection(
                seg_w, colors=col_w, linewidths=0.8,
                alpha=0.5 * (1 - t) ** 1.2, zorder=3, capstyle="round"))

        if t >= 1.0:
            # final panel: explicit super-edges, width from block means
            seg, lws = [], []
            for a, ka in enumerate(present):
                for b in range(a + 1, K):
                    lw = 5.0 * B[a, b] / bmax
                    if lw < 0.3:
                        continue
                    seg.append([cent[ka], cent[present[b]]])
                    lws.append(lw)
            pax.add_collection(LineCollection(
                seg, colors=INK["axis"], linewidths=lws, zorder=3,
                capstyle="round"))

        # super-nodes fade in as the regions fade out
        if t > 0.35:
            a_super = min(1.0, (t - 0.35) / 0.65)
            for k in present:
                pax.add_patch(plt.Circle(
                    cent[k], radius[k], facecolor=cs.community_color(k),
                    edgecolor=cs.SURFACE[MODE], linewidth=1.3,
                    alpha=a_super, zorder=4))
        if t >= 1.0:
            for k in present:
                pax.text(cent[k][0], cent[k][1], str(k + 1), ha="center",
                         va="center", fontsize=cs.TYPE["caption"],
                         weight="semibold", color=cs.SURFACE[MODE], zorder=6)

        # individual regions
        if t < 1.0:
            a_node = 1.0 if t < 0.35 else max(0.06, 1 - (t - 0.35) / 0.65)
            figviz.draw_nodes(pax, P, assign, node_s, mode=MODE, ring=0.6,
                              zorder=5, alpha=a_node)

        x0 = ax.get_position().x0
        fig.text(x0, 0.845, head, fontsize=cs.TYPE["panel_title"],
                 weight="semibold", color=INK["primary"], va="baseline")
        fig.text(x0, 0.800, sub, fontsize=cs.TYPE["caption"],
                 color=INK["secondary"], va="baseline")

    handles = [Line2D([], [], marker="o", linestyle="none", markersize=6,
                      markerfacecolor=cs.community_color(k),
                      markeredgecolor=cs.SURFACE[MODE], markeredgewidth=0.8,
                      label=f"{k + 1}  ({sizes[k]})") for k in present]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.028, 0.005),
               ncol=K, frameon=False, fontsize=cs.TYPE["caption"],
               handletextpad=0.4, columnspacing=1.2,
               title="Community (regions)",
               title_fontsize=cs.TYPE["caption"])
    fig.legends[0].get_title().set_color(INK["muted"])

    fig.text(0.978, 0.020,
             f"axial view · strongest {100 - EDGE_PCT:.0f}% of edges "
             f"({n_kept} of {n_tot}) · super-node area scales with region count",
             fontsize=cs.TYPE["caption"], color=INK["muted"], ha="right",
             va="bottom")

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure5_connectome_collapsed.pdf"))
    fig.savefig(os.path.join(OUT, "figure5_connectome_collapsed.png"), dpi=400)
    plt.close(fig)
    print(f"  stages: {[s[0] for s in STAGES]}")
    print(f"  edges morphed: {n_kept} of {n_tot} "
          f"({int(same.sum())} within, {int((~same).sum())} between)")
    print("  wrote figures/figure5_connectome_collapsed.{pdf,png}")


if __name__ == "__main__":
    main()
