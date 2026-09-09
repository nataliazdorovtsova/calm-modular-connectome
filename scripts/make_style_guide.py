#!/usr/bin/env python
"""
Render the CALM project style guide.

Page 1  the system   -- palette, ramps, typography, chrome, mark specs
Page 2  the system applied -- the same six communities tracked across the three
                              representational spaces the proposal demands
                              (anatomy -> matrix -> community graph)

Page 2 uses REAL data: the group-average CALM 800 connectome, Louvain
communities, and true MNI coordinates. It is therefore also an end-to-end check
that the environment works.

    env/bin/python scripts/make_style_guide.py
"""

import glob
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, FancyArrowPatch

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
from style import calm_style as cs  # noqa: E402

DATA = os.path.join(PROJ, "data")
OUT = os.path.join(PROJ, "figures")
MODE = "light"
INK = cs.INK[MODE]


# ------------------------------------------------------------------ real data

def load_group_average():
    """Mean connectome over the CALM 800 subjects, plus labels and coords."""
    files = sorted(glob.glob(os.path.join(
        DATA, "connectomes_schaefer100x17_count", "sub-*.csv")))
    total, n = None, 0
    for f in files:
        m = np.loadtxt(f, delimiter=",", skiprows=1,
                       usecols=range(1, 101), dtype=float)
        total = m if total is None else total + m
        n += 1
    mean = total / n

    labels, coords = [], []
    with open(os.path.join(DATA, "region_labels_schaefer100x17.csv")) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split(",")
            labels.append(p[1])
            coords.append([float(p[2]), float(p[3]), float(p[4])])
    return mean, labels, np.array(coords), n


def detect_communities(W, seed=0):
    """Louvain on the group-average, capped at the palette's six slots."""
    import networkx as nx
    G = nx.from_numpy_array(W)
    comms = nx.community.louvain_communities(G, weight="weight", seed=seed,
                                             resolution=1.0)
    comms = sorted(comms, key=len, reverse=True)
    assign = np.full(W.shape[0], cs.MAX_COMMUNITIES, dtype=int)
    for k, nodes in enumerate(comms):
        for nd in nodes:
            assign[nd] = k if k < cs.MAX_COMMUNITIES else cs.MAX_COMMUNITIES
    return assign, len(comms)


# ------------------------------------------------------------- page 1 helpers

def panel_palette(ax):
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.4)
    ax.text(0, 3.15, "Community palette", fontsize=cs.TYPE["panel_title"],
            weight="semibold", color=INK["primary"], va="bottom")
    ax.text(0, 2.92, "Okabe-Ito, fixed slot order. Slot k belongs to community "
                     "k in every figure — never cycled, never re-ranked.",
            fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="bottom")
    w = 1.24
    for i, (name, hexv) in enumerate(cs.COMMUNITIES.items()):
        x = i * (w + 0.16)
        ax.add_patch(Rectangle((x, 1.42), w, 1.18, facecolor=hexv,
                               edgecolor=cs.SURFACE[MODE], linewidth=1.4))
        ax.text(x, 1.22, f"{i + 1}  {name}", fontsize=cs.TYPE["annotation"],
                color=INK["primary"], va="top", weight="semibold")
        ax.text(x, 0.98, hexv, fontsize=cs.TYPE["caption"],
                color=INK["muted"], va="top", family="monospace")
    x = cs.MAX_COMMUNITIES * (w + 0.16)
    ax.add_patch(Rectangle((x, 1.42), w, 1.18, facecolor=cs.OTHER,
                           edgecolor=cs.SURFACE[MODE], linewidth=1.4))
    ax.text(x, 1.22, "—  other", fontsize=cs.TYPE["annotation"],
            color=INK["primary"], va="top", weight="semibold")
    ax.text(x, 0.98, cs.OTHER, fontsize=cs.TYPE["caption"],
            color=INK["muted"], va="top", family="monospace")
    ax.text(0, 0.42, "Validated all-pairs (any two communities may sit adjacent "
                     "in a brain render):  worst CVD ΔE 7.6  ·  worst "
                     "normal-vision ΔE 15.6  ·  PASS",
            fontsize=cs.TYPE["caption"], color=INK["secondary"], va="bottom")
    ax.text(0, 0.10, "ΔE 7.6 is in the 6–8 floor band → secondary "
                     "encoding is MANDATORY: block boundaries, colour bars, "
                     "direct labels, or facets. Six is a cap, not a default.",
            fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")


def panel_ramps(ax):
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 2.6)
    ax.text(0, 2.35, "Magnitude and polarity",
            fontsize=cs.TYPE["panel_title"], weight="semibold",
            color=INK["primary"], va="bottom")
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(grad, extent=(0, 4.6, 1.58, 2.00), aspect="auto",
              cmap=cs.sequential_cmap())
    ax.text(0, 1.44, "Sequential — one hue, light→dark. "
                     "Connectivity magnitude.",
            fontsize=cs.TYPE["caption"], color=INK["secondary"], va="top")
    ax.imshow(grad, extent=(5.4, 10, 1.58, 2.00), aspect="auto",
              cmap=cs.diverging_cmap(mode=MODE))
    ax.text(5.4, 1.44, "Diverging — two hues, NEUTRAL grey midpoint. "
                       "Within − between, group contrasts.",
            fontsize=cs.TYPE["caption"], color=INK["secondary"], va="top")
    ax.text(0, 0.62, "Never a rainbow. Never a hue at the diverging midpoint. "
                     "Magnitude is never encoded with the community palette — "
                     "that channel carries identity only.",
            fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")


def panel_type(ax):
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.2)
    ax.text(0, 2.95, "Typography", fontsize=cs.TYPE["panel_title"],
            weight="semibold", color=INK["primary"], va="bottom")
    ax.text(0, 2.72, "Lato, installed cluster-wide. Fallbacks: Liberation Sans, "
                     "DejaVu Sans. Figures authored at 180 mm width.",
            fontsize=cs.TYPE["annotation"], color=INK["secondary"], va="bottom")
    rows = [("Figure title", "figure_title", "semibold", INK["primary"]),
            ("Panel title", "panel_title", "semibold", INK["primary"]),
            ("Axis label", "axis_label", "normal", INK["secondary"]),
            ("Tick / annotation", "tick", "normal", INK["secondary"]),
            ("Caption", "caption", "normal", INK["muted"])]
    y = 2.30
    for label, key, weight, color in rows:
        ax.text(0, y, f"{label}", fontsize=cs.TYPE[key], weight=weight,
                color=color, va="center")
        ax.text(6.4, y, f"{cs.TYPE[key]:.1f} pt", fontsize=cs.TYPE["caption"],
                color=INK["muted"], va="center", family="monospace")
        ax.text(8.2, y, weight, fontsize=cs.TYPE["caption"],
                color=INK["muted"], va="center")
        y -= 0.44
    ax.text(0, 0.10, "Text always wears ink tokens — never a community "
                     "colour. A coloured mark beside the label carries identity.",
            fontsize=cs.TYPE["caption"], color=INK["muted"], va="bottom")


def panel_chrome(ax):
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.2)
    ax.text(0, 2.95, "Ink & chrome", fontsize=cs.TYPE["panel_title"],
            weight="semibold", color=INK["primary"], va="bottom")
    roles = [("primary ink", INK["primary"]), ("secondary ink", INK["secondary"]),
             ("muted / axis labels", INK["muted"]), ("gridline", INK["grid"]),
             ("baseline / axis", INK["axis"]), ("context node", cs.CONTEXT_NODE),
             ("chart surface", cs.SURFACE[MODE])]
    y = 2.52
    for name, hexv in roles:
        ax.add_patch(Rectangle((0, y - 0.13), 0.52, 0.28, facecolor=hexv,
                               edgecolor=INK["grid"], linewidth=0.6))
        ax.text(0.72, y, name, fontsize=cs.TYPE["annotation"],
                color=INK["secondary"], va="center")
        ax.text(4.0, y, hexv, fontsize=cs.TYPE["caption"], color=INK["muted"],
                va="center", family="monospace")
        y -= 0.36
    ax.text(5.6, 2.52, "Marks", fontsize=cs.TYPE["annotation"],
            weight="semibold", color=INK["primary"], va="center")
    specs = ["2.0 pt lines, round caps", "≥ 4 pt markers (8 px)",
             "0.6 pt axes, no top/right spine", "hairline grid, always behind",
             "2 px surface ring on overlaps", "legend always ≥ 2 series"]
    y = 2.16
    for s in specs:
        ax.text(5.6, y, "·  " + s, fontsize=cs.TYPE["caption"],
                color=INK["secondary"], va="center")
        y -= 0.30


# ------------------------------------------------------------- page 2 helpers

def panel_anatomy(ax, coords, assign, W):
    ax.set_axis_off()
    ax.set_aspect("equal")
    thr = np.percentile(W[W > 0], 96)
    iu = np.triu_indices_from(W, 1)
    for i, j in zip(*iu):
        if W[i, j] >= thr:
            ax.plot([coords[i, 1], coords[j, 1]], [coords[i, 2], coords[j, 2]],
                    color=cs.CONTEXT_EDGE, linewidth=0.4, zorder=1,
                    solid_capstyle="round")
    for k in range(cs.MAX_COMMUNITIES + 1):
        sel = assign == k
        if not sel.any():
            continue
        ax.scatter(coords[sel, 1], coords[sel, 2], s=34,
                   c=cs.community_color(k), edgecolors=cs.SURFACE[MODE],
                   linewidths=0.8, zorder=3)
    # A legend is mandatory whenever >= 2 communities are shown: the CVD floor
    # band means identity must never rest on colour alone.
    present = [k for k in range(cs.MAX_COMMUNITIES + 1) if (assign == k).any()]
    labels = [(f"Community {k + 1}" if k < cs.MAX_COMMUNITIES else "Other")
              + f"  ({(assign == k).sum()})" for k in present]
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=5.5,
                      markerfacecolor=cs.community_color(k),
                      markeredgecolor=cs.SURFACE[MODE], markeredgewidth=0.8,
                      label=lab) for k, lab in zip(present, labels)]
    ax.legend(handles=handles, loc="lower left", frameon=False, ncol=2,
              fontsize=cs.TYPE["caption"], handletextpad=0.5,
              columnspacing=1.0, labelspacing=0.45,
              bbox_to_anchor=(-0.02, -0.16))
    ax.set_title("Anatomical space", fontsize=cs.TYPE["panel_title"],
                 weight="semibold", color=INK["primary"], loc="left", pad=20)
    ax.annotate("sagittal view, top 4% of edges",
                xy=(0, 1), xycoords="axes fraction", xytext=(0, 5),
                textcoords="offset points", fontsize=cs.TYPE["caption"],
                color=INK["secondary"], ha="left", va="bottom")


def panel_matrix(ax, W, assign):
    order, bounds, _ = cs.order_by_community(assign)
    M = W[np.ix_(order, order)]
    shown = np.log1p(M)
    ax.imshow(shown, cmap=cs.sequential_cmap(), interpolation="nearest",
              vmin=0, vmax=np.percentile(shown, 99.5))
    cs.community_colorbars(ax, assign, order, mode=MODE)
    cs.draw_community_blocks(ax, bounds, len(assign), mode=MODE, lw=0.8)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Connectivity space", fontsize=cs.TYPE["panel_title"],
                 weight="semibold", color=INK["primary"], loc="left", pad=20)
    ax.annotate("region × region, reordered by community; "
                "log streamline count",
                xy=(0, 1), xycoords="axes fraction", xytext=(0, 5),
                textcoords="offset points", fontsize=cs.TYPE["caption"],
                color=INK["secondary"], ha="left", va="bottom")


def panel_graph(ax, W, assign):
    ax.set_axis_off(); ax.set_aspect("equal")
    ks = [k for k in range(cs.MAX_COMMUNITIES + 1) if (assign == k).any()]
    n = len(ks)
    B = np.zeros((n, n))
    for a, ka in enumerate(ks):
        for b, kb in enumerate(ks):
            B[a, b] = W[np.ix_(assign == ka, assign == kb)].mean()
    ang = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, n, endpoint=False)
    pos = np.c_[np.cos(ang), np.sin(ang)]
    mx = B[~np.eye(n, dtype=bool)].max()
    for a in range(n):
        for b in range(a + 1, n):
            lw = 6.0 * B[a, b] / mx
            if lw < 0.25:
                continue
            ax.plot(*zip(pos[a], pos[b]), color=INK["grid"], linewidth=lw,
                    zorder=1, solid_capstyle="round")
    sizes = [(assign == k).sum() for k in ks]
    for a, k in enumerate(ks):
        r = 0.055 + 0.115 * sizes[a] / max(sizes)
        ax.add_patch(plt.Circle(pos[a], r, facecolor=cs.community_color(k),
                                edgecolor=cs.SURFACE[MODE], linewidth=1.6,
                                zorder=3))
        lab = f"{k + 1}" if k < cs.MAX_COMMUNITIES else "—"
        ax.text(*pos[a], lab, ha="center", va="center", zorder=4,
                fontsize=cs.TYPE["annotation"], weight="semibold",
                color=cs.SURFACE[MODE])
        ax.text(pos[a][0] * 1.42, pos[a][1] * 1.42, f"{sizes[a]} regions",
                ha="center", va="center", fontsize=cs.TYPE["caption"],
                color=INK["secondary"])
    ax.set_xlim(-1.75, 1.75); ax.set_ylim(-1.6, 1.7)
    ax.set_title("Community space", fontsize=cs.TYPE["panel_title"],
                 weight="semibold", color=INK["primary"], loc="left", pad=20)
    ax.annotate("node size = regions; edge width = mean connectivity",
                xy=(0, 1), xycoords="axes fraction", xytext=(0, 5),
                textcoords="offset points", fontsize=cs.TYPE["caption"],
                color=INK["secondary"], ha="left", va="bottom")


# ------------------------------------------------------------------- assembly

def page1(pdf):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.055, 0.960, "CALM connectome figures — style guide",
             fontsize=15, weight="semibold", color=INK["primary"])
    fig.text(0.055, 0.941, "One palette, one type scale, one set of chrome "
                           "rules, applied to every figure in the project.",
             fontsize=cs.TYPE["annotation"], color=INK["secondary"])
    fig.text(0.055, 0.924, "Part 1 · the system",
             fontsize=cs.TYPE["caption"], color=INK["muted"])
    gs = fig.add_gridspec(4, 1, left=0.055, right=0.955, top=0.895, bottom=0.05,
                          hspace=0.14,
                          height_ratios=[3.4, 2.6, 3.2, 3.2])
    panel_palette(fig.add_subplot(gs[0]))
    panel_ramps(fig.add_subplot(gs[1]))
    panel_type(fig.add_subplot(gs[2]))
    panel_chrome(fig.add_subplot(gs[3]))
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "style_guide_p1.png"))
    plt.close(fig)


def page2(pdf, W, coords, assign, n_sub, n_comm):
    fig = plt.figure(figsize=(11.69, 6.7))
    fig.text(0.045, 0.940, "The same six communities, three representations",
             fontsize=15, weight="semibold", color=INK["primary"])
    fig.text(0.045, 0.902,
             "Group-average CALM 800 connectome (n = %d), Schaefer 100×17, "
             "streamline counts. Louvain found %d communities."
             % (n_sub, n_comm),
             fontsize=cs.TYPE["annotation"], color=INK["secondary"])
    fig.text(0.045, 0.870, "Part 2 · the system applied",
             fontsize=cs.TYPE["caption"], color=INK["muted"])
    gs = fig.add_gridspec(1, 3, left=0.045, right=0.965, top=0.800,
                          bottom=0.175, wspace=0.16)
    panel_anatomy(fig.add_subplot(gs[0]), coords, assign, W)
    panel_matrix(fig.add_subplot(gs[1]), W, assign)
    panel_graph(fig.add_subplot(gs[2]), W, assign)

    for x in (0.345, 0.655):
        fig.patches.append(FancyArrowPatch(
            (x, 0.49), (x + 0.022, 0.49), transform=fig.transFigure,
            arrowstyle="-|>", mutation_scale=13, color=INK["muted"], lw=0.9))
    fig.text(0.045, 0.045,
             "Community identity is invariant across the three spaces — that "
             "invariance is the whole point of fixing the palette. Every panel "
             "carries secondary encoding (block\nboundaries and colour bars on "
             "the matrix, numbered super-nodes on the graph), which the CVD "
             "floor band makes mandatory rather than optional.",
             fontsize=cs.TYPE["caption"], color=INK["secondary"])
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "style_guide_p2.png"))
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    cs.use_style(MODE)
    print("loading group-average connectome ...")
    W, labels, coords, n_sub = load_group_average()
    print(f"  averaged {n_sub} subjects, matrix {W.shape}")
    assign, n_comm = detect_communities(W)
    sizes = [(assign == k).sum() for k in range(cs.MAX_COMMUNITIES + 1)]
    print(f"  Louvain communities: {n_comm}  sizes(by slot): {sizes}")
    out_pdf = os.path.join(OUT, "style_guide.pdf")
    with PdfPages(out_pdf) as pdf:
        page1(pdf)
        page2(pdf, W, coords, assign, n_sub, n_comm)
    print("wrote", out_pdf)
    np.savetxt(os.path.join(DATA, "group_average_schaefer100x17.csv"), W,
               delimiter=",", fmt="%.6f")
    np.savetxt(os.path.join(DATA, "community_assignments_groupavg.csv"),
               np.c_[np.arange(1, 101), assign], delimiter=",", fmt="%d",
               header="region_index,community_slot", comments="")
    print("wrote group average + community assignments")


if __name__ == "__main__":
    main()
