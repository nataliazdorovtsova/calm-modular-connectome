#!/usr/bin/env python
"""
Figure 6 — The network of networks.

A circular connectogram. All 100 regions sit on the ring, ordered by community
and then by anatomical network, each labelled. Community arcs outside the ring
are the "nodes" of the network of networks; the chords crossing the interior are
their relationships.

Only BETWEEN-community connections are drawn. Within-community edges are what
the previous five figures were about, and including them here would fill the
disc with the connections we already know are dense. What is left is exactly the
higher-level structure the proposal asks for: which specific regions carry
traffic between which communities.

As in Figure 5, the aggregate is left to assemble itself. Chords are drawn per
region pair, not per community pair, so a thick visual bundle between two arcs
IS the community-level relationship, and a missing bundle is a real absence
rather than a thresholding decision.

Chords are grey, not community-coloured, on purpose. A chord has two community
endpoints, so painting it one community's colour would claim an identity it
does not have; the palette stays on the arcs, where identity is unambiguous, and
the chord spends its width on magnitude instead.

    env/bin/python scripts/make_figure6.py
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
from matplotlib.patches import PathPatch, Wedge
from matplotlib.collections import PatchCollection

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

R_TICK = 1.00          # region ticks
R_ARC_IN = 1.045       # community arc
R_ARC_OUT = 1.085
R_LABEL = 1.115        # region labels start here
N_CHORDS = 70          # strongest between-community edges to draw
GAP_DEG = 2.6          # gap between community arcs

#: Schaefer 17-network names are too long to ring a circle; these keep the
#: anatomy legible at 5 pt.
NET_ABBREV = {
    "VisCent": "Vis-C", "VisPeri": "Vis-P",
    "SomMotA": "SomMot-A", "SomMotB": "SomMot-B",
    "DorsAttnA": "dAttn-A", "DorsAttnB": "dAttn-B",
    "SalVentAttnA": "vAttn-A", "SalVentAttnB": "vAttn-B",
    "Limbic": "Limbic", "TempPar": "TempPar",
    "ContA": "Cont-A", "ContB": "Cont-B", "ContC": "Cont-C",
    "DefaultA": "Def-A", "DefaultB": "Def-B", "DefaultC": "Def-C",
}


def short_label(name):
    """'LH_VisCent_ExStr_1' -> 'L Vis-C ExStr 1'."""
    parts = name.split("_")
    hemi = "L" if parts[0] == "LH" else "R"
    net = NET_ABBREV.get(parts[1], parts[1])
    rest = " ".join(parts[2:])
    return f"{hemi} {net} {rest}".strip()


def chord(p1, p2, pull=0.42):
    """Cubic bezier between two ring points, bowed toward the centre.

    Widely separated endpoints are pulled in harder so long chords do not
    crowd the ring and short ones keep a readable arc.
    """
    sep = np.arccos(np.clip(np.dot(p1, p2) /
                            (np.linalg.norm(p1) * np.linalg.norm(p2)), -1, 1))
    k = pull * (1 - 0.55 * (1 - sep / np.pi))
    return Path([p1, p1 * k, p2 * k, p2],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])


def main():
    W = cd.group_average()
    assign = cd.communities()
    names = cd.region_labels()
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)
    n = len(assign)

    # order: community, then anatomical network, then region index
    order = sorted(range(n), key=lambda i: (assign[i], names[i].split("_")[1],
                                            names[i]))
    pos_of = {i: p for p, i in enumerate(order)}

    # angles, with a gap between communities
    total_gap = GAP_DEG * len(present)
    span = (360.0 - total_gap) / n
    ang = np.zeros(n)
    cur = 90.0
    bounds = {}
    for k in present:
        start = cur
        for i in [j for j in order if assign[j] == k]:
            ang[i] = cur - span / 2
            cur -= span
        bounds[k] = (start, cur)
        cur -= GAP_DEG

    def xy(a_deg, r):
        t = np.radians(a_deg)
        return np.array([r * np.cos(t), r * np.sin(t)])

    # strongest between-community edges
    iu = np.triu_indices(n, 1)
    between = assign[iu[0]] != assign[iu[1]]
    bi, bj, bw = iu[0][between], iu[1][between], W[iu][between]
    take = np.argsort(bw)[::-1][:N_CHORDS]
    bi, bj, bw = bi[take], bj[take], bw[take]

    cs.use_style(MODE)
    fig = plt.figure(figsize=(7.09, 7.35))
    ax = fig.add_axes([0.055, 0.045, 0.89, 0.845])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_xlim(-1.52, 1.52)
    ax.set_ylim(-1.52, 1.52)

    fig.text(0.038, 0.975, "The network of networks", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")
    fig.text(0.038, 0.943,
             "All 100 regions on the ring, grouped by community then by "
             "anatomical network. Chords are the "
             f"{N_CHORDS} strongest\nbetween-community connections; "
             "within-community connections are omitted, so what remains is "
             "the higher-level structure.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="top",
             linespacing=1.5)

    # ---- chords (behind everything) ---------------------------------------
    wmax = bw.max()
    for i, j, w in zip(bi, bj, bw):
        p1, p2 = xy(ang[i], R_TICK), xy(ang[j], R_TICK)
        lw = 0.35 + 2.6 * (w / wmax) ** 0.6
        ax.add_patch(PathPatch(chord(p1, p2), facecolor="none",
                               edgecolor=cs.CONTEXT_EDGE, linewidth=lw,
                               alpha=0.95, zorder=2, capstyle="round"))

    # ---- community arcs = the nodes of the network of networks ------------
    wedges, wcolors = [], []
    for k in present:
        a1, a2 = bounds[k]
        wedges.append(Wedge((0, 0), R_ARC_OUT, min(a1, a2), max(a1, a2),
                            width=R_ARC_OUT - R_ARC_IN))
        wcolors.append(cs.community_color(k))
    ax.add_collection(PatchCollection(wedges, facecolors=wcolors,
                                      edgecolors="none", zorder=4))

    # ---- region ticks -----------------------------------------------------
    for i in range(n):
        p = xy(ang[i], R_TICK)
        ax.plot([p[0] * 0.982, p[0] * 1.018], [p[1] * 0.982, p[1] * 1.018],
                color=cs.community_color(int(assign[i])), linewidth=1.1,
                solid_capstyle="butt", zorder=3)

    # ---- region labels ----------------------------------------------------
    for i in range(n):
        a = ang[i]
        p = xy(a, R_LABEL)
        rot = a if -90 <= a <= 90 else a + 180
        ha = "left" if -90 <= a <= 90 else "right"
        ax.text(p[0], p[1], short_label(names[i]), rotation=rot,
                rotation_mode="anchor", ha=ha, va="center",
                fontsize=5.0, color=INK["secondary"], zorder=5)

    # ---- community identity ----------------------------------------------
    # The number rides on its own arc and the sizes go in a legend. Spelling
    # "Community k, n regions" around the rim put it at the same radius as the
    # region labels, where the two collided.
    for k in present:
        a1, a2 = bounds[k]
        mid = (a1 + a2) / 2
        p = xy(mid, (R_ARC_IN + R_ARC_OUT) / 2)
        ax.text(p[0], p[1], str(k + 1), ha="center", va="center",
                fontsize=cs.TYPE["caption"], weight="semibold",
                color=cs.SURFACE[MODE], zorder=6)

    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=6,
                      markerfacecolor=cs.community_color(k),
                      markeredgecolor=cs.SURFACE[MODE], markeredgewidth=0.8,
                      label=f"{k + 1}  ({sizes[k]})") for k in present]
    leg = fig.legend(handles=handles, loc="upper right",
                     bbox_to_anchor=(0.962, 0.972), ncol=1, frameon=False,
                     fontsize=cs.TYPE["caption"], handletextpad=0.5,
                     labelspacing=0.55, title="Community (regions)",
                     title_fontsize=cs.TYPE["caption"])
    leg.get_title().set_color(INK["muted"])

    n_12 = int(sum(1 for i, j in zip(bi, bj)
                   if {int(assign[i]), int(assign[j])} == {0, 1}))
    fig.text(0.038, 0.014,
             "Chord width is streamline count. Chords are grey rather than "
             "community-coloured: a chord has two community endpoints, so the "
             "palette stays on the arcs\nwhere identity is unambiguous. "
             f"Communities 1 and 2 — wholly left and wholly right — take only "
             f"{n_12} of these {N_CHORDS} chords between them.",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom",
             linespacing=1.5)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure6_network_of_networks.pdf"))
    fig.savefig(os.path.join(OUT, "figure6_network_of_networks.png"), dpi=400)
    plt.close(fig)

    # which community pairs actually carry the drawn chords
    print(f"  drew {len(bi)} between-community chords "
          f"(weights {bw.min():.0f}–{bw.max():.0f})")
    from collections import Counter
    cnt = Counter(tuple(sorted((int(assign[i]) + 1, int(assign[j]) + 1)))
                  for i, j in zip(bi, bj))
    for pair, c in sorted(cnt.items()):
        print(f"    {pair[0]}–{pair[1]}: {c} chords")
    missing = [(a + 1, b + 1) for ai, a in enumerate(present)
               for b in present[ai + 1:]
               if tuple(sorted((a + 1, b + 1))) not in cnt]
    print(f"  community pairs with no chord in the top {N_CHORDS}: {missing}")
    print("  wrote figures/figure6_network_of_networks.{pdf,png}")


if __name__ == "__main__":
    main()
