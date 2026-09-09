#!/usr/bin/env python
"""
Figure 3 — Communities in anatomical space.

One column per community: its regions in colour against the rest of the brain
in muted grey, in two views. Faceting is doing real work here, not just
decoration -- it is also the escape hatch the colour gate requires, since one
community per panel means no two community colours are ever compared directly.

The proposal asks whether communities are "compact, distributed, or spatially
heterogeneous". That is measurable, so it is measured rather than eyeballed:

    dispersion = mean Euclidean distance (mm) of a community's regions from
                 their own centroid

and compared against a null built by drawing random region sets of the same
size from the same 100 coordinates. A dispersion far below the null means the
community is spatially compact; one indistinguishable from the null means the
partition is not respecting anatomy at all.

    env/bin/python scripts/make_figure3.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import numpy as np
import matplotlib.pyplot as plt

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs      # noqa: E402
import calm_data as cd                  # noqa: E402
import figviz                           # noqa: E402

OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]

EDGE_PCT = 90.0        # within-community edges are sparser, so show more
N_PERM = 20000
VIEWS = [("z", "Axial"), ("l", "Sagittal")]


def dispersion(coords, idx):
    """Mean distance (mm) from the centroid of the selected regions."""
    pts = coords[idx]
    return float(np.linalg.norm(pts - pts.mean(0), axis=1).mean())


def dispersion_null(coords, n, n_perm=N_PERM, seed=0):
    rng = np.random.default_rng(seed)
    N = len(coords)
    out = np.empty(n_perm)
    for t in range(n_perm):
        out[t] = dispersion(coords, rng.choice(N, size=n, replace=False))
    return out


def main():
    W = cd.group_average()
    assign = cd.communities()
    coords = cd.coordinates()
    names = cd.region_labels()
    present = cd.present_communities(assign)
    sizes = cd.community_sizes(assign)

    pairs, _, n_kept, n_tot = figviz.top_edges(W, EDGE_PCT)

    deg = W.sum(1)
    node_s = 9 + 26 * (deg - deg.min()) / (deg.max() - deg.min())

    # ---- is each community spatially compact? ------------------------------
    stats = {}
    for k in present:
        idx = np.flatnonzero(assign == k)
        obs = dispersion(coords, idx)
        null = dispersion_null(coords, len(idx))
        p = float((null <= obs).mean())
        lh = sum(1 for i in idx if names[i].startswith("LH"))
        stats[k] = dict(disp=obs, null_mean=null.mean(), p=p,
                        lh=lh, rh=len(idx) - lh)
        print(f"  community {k+1}: dispersion {obs:5.1f} mm  "
              f"(null {null.mean():5.1f})  p={p:.4f}  "
              f"{lh}L/{len(idx)-lh}R")

    cs.use_style(MODE)
    ncol = len(present)
    fig = plt.figure(figsize=(7.09, 5.6))

    fig.text(0.045, 0.965, "Communities in anatomical space", fontsize=13,
             weight="semibold", color=INK["primary"], va="top")

    gs = fig.add_gridspec(2, ncol, left=0.055, right=0.985, top=0.850,
                          bottom=0.335, hspace=0.04, wspace=0.03,
                          height_ratios=[1.42, 1.0])

    for col, k in enumerate(present):
        sel = assign == k
        for row, (direction, _) in enumerate(VIEWS):
            ax = fig.add_subplot(gs[row, col])
            pax = figviz.glass_panel(ax, direction, alpha=0.09)
            P = figviz.project(coords, direction)
            # context: the rest of the brain, present but recessive
            figviz.draw_nodes(pax, P, assign, node_s * 0.55, show=~sel,
                              mode=MODE, ring=0.0, zorder=2,
                              color_override=cs.CONTEXT_NODE)
            # this community only
            figviz.draw_edges(pax, P, pairs, assign, show=sel,
                              within_lw=0.75, within_alpha=0.5,
                              only_within=True)
            figviz.draw_nodes(pax, P, assign, node_s, show=sel, mode=MODE,
                              ring=0.6, zorder=5)
            if col == 0:
                ax.annotate(VIEWS[row][1], xy=(0, 0.5),
                            xycoords="axes fraction", xytext=(-8, 0),
                            textcoords="offset points",
                            fontsize=cs.TYPE["caption"], color=INK["muted"],
                            ha="right", va="center", rotation=90)

        # column header: swatch + label, so identity is never colour alone
        x0 = 0.055 + (col + 0.5) * (0.985 - 0.055) / ncol
        fig.text(x0, 0.892, f"Community {k + 1}", ha="center", va="bottom",
                 fontsize=cs.TYPE["annotation"], weight="semibold",
                 color=INK["primary"])
        fig.text(x0, 0.872, f"{sizes[k]} regions", ha="center", va="bottom",
                 fontsize=cs.TYPE["caption"], color=INK["muted"])
        fig.patches.append(plt.Circle(
            (x0 - 0.052, 0.9015), 0.0055, transform=fig.transFigure,
            facecolor=cs.community_color(k), edgecolor="none", zorder=5))

        # footer: the compactness result
        st = stats[k]
        lat = (f"{st['lh']} L" if st["rh"] == 0 else
               f"{st['rh']} R" if st["lh"] == 0 else
               f"{st['lh']} L / {st['rh']} R")
        ptxt = "p < 0.0001" if st["p"] < 1e-4 else f"p = {st['p']:.3f}"
        fig.text(x0, 0.246, f"{st['disp']:.0f} mm", ha="center", va="center",
                 fontsize=cs.TYPE["annotation"], weight="semibold",
                 color=INK["primary"])
        fig.text(x0, 0.205, f"vs {st['null_mean']:.0f} by chance",
                 ha="center", va="center", fontsize=cs.TYPE["caption"],
                 color=INK["secondary"])
        fig.text(x0, 0.172, ptxt, ha="center", va="center",
                 fontsize=cs.TYPE["caption"], color=INK["secondary"])
        fig.text(x0, 0.131, lat, ha="center", va="center",
                 fontsize=cs.TYPE["caption"], color=INK["muted"])

    fig.text(0.045, 0.293, "Spatial dispersion — mean distance of a "
             "community's regions from their own centroid",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="center")
    fig.text(0.045, 0.022,
             f"Regions of one community in colour against the rest of the "
             f"brain in grey; within-community connections only "
             f"(strongest {100 - EDGE_PCT:.0f}%). Node size is weighted "
             f"degree.\nDispersion null: {N_PERM:,} random region sets of "
             f"matched size drawn from the same 100 coordinates.",
             fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom",
             linespacing=1.5)

    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "figure3_anatomical_space.pdf"))
    fig.savefig(os.path.join(OUT, "figure3_anatomical_space.png"), dpi=400)
    plt.close(fig)
    print(f"  within-community edges shown: {n_kept} of {n_tot}")
    print("  wrote figures/figure3_anatomical_space.{pdf,png}")


if __name__ == "__main__":
    main()
