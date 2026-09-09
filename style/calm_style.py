"""
CALM modular-connectome visual style.

One import gives every figure in the project the same palette, typography and
chrome, so a community keeps its identity as the reader moves from an anatomical
render to a matrix to an abstract community graph.

    import sys, os; sys.path.insert(0, "<project root>")
    from style import calm_style as cs

    cs.use_style()                       # light (publication) by default
    fig, ax = plt.subplots()
    ax.scatter(x, y, color=cs.community_color(0))
    cs.finish(ax, title="Figure 1", subtitle="Modular connectome")

--------------------------------------------------------------------------
WHY THIS PALETTE  (the numbers, not the taste)
--------------------------------------------------------------------------
Community colour in this project is read in an ALL-PAIRS setting: in a brain
render any two communities can end up adjacent, so *every* pair must separate,
not just neighbouring ones. That is a much harder gate than the adjacent-only
case that applies to bars and stacks.

Measured with the data-viz validator (OKLab dE x100, Machado-Oliveira-Fernandes
2009 CVD simulation at severity 1.0, all-pairs):

    Okabe-Ito 6      worst CVD dE 7.6   worst normal-vision dE 15.6   PASS
    Okabe-Ito 7      FAILS  (yellow #F0E442 breaks the lightness band and
                             sits at 1.29:1 contrast on white)
    Tol bright 6     FAILS  (lightness band + chroma floor)
    Tol muted 6      FAILS  (CVD dE 5.2)
    reference 8-hue  FAILS at 4 slots (normal-vision dE 13.7)

A pure max-min search over OKLCH space does score higher (dE 17.2), but it
returns three blues and three greens -- it buys separation with lightness and
spends all the hue variety, which is precisely the channel this project needs a
reader to track across six figures. Okabe-Ito is kept: it is the published
standard for colourblind-safe scientific figures, it is hue-varied, and it
clears every hard gate.

CVD dE 7.6 sits in the 6-8 "floor" band, which is legal ONLY with secondary
encoding. So secondary encoding is MANDATORY here, never decorative:
community boundaries and colour bars on matrices, direct labels on community
graphs, and the faceted one-community-per-panel treatment for anatomy.
Three light-mode colours are also sub-3:1 on white (orange 2.19, sky blue 2.25,
reddish purple 2.98), which obliges visible labels under the same rule.

SIX COMMUNITIES IS A CAP, NOT A DEFAULT. A 7th community must fold into
OTHER (grey) or be faceted -- adding a 7th hue breaks the gate above. Tune the
community-detection resolution to land at <= 6, or merge the smallest modules.

Dark mode deliberately reuses the *same* hexes. On the dark surface all six
clear 3:1 contrast and the CVD/normal-vision separations are unchanged; only
the reference lightness band complains, and that band's purpose -- marks
readable against the surface -- is already verified directly by the contrast
check. Holding the hexes fixed means a community's colour is literally
invariant across paper, screen and slides, which is the point of the project.
"""

from collections import OrderedDict

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

# ---------------------------------------------------------------- communities

#: Fixed slot order. NEVER cycle, never reorder, never recolour by rank --
#: community k takes slot k in every figure, in every representation.
COMMUNITIES = OrderedDict([
    ("orange",         "#E69F00"),
    ("sky blue",       "#56B4E9"),
    ("bluish green",   "#009E73"),
    ("blue",           "#0072B2"),
    ("vermillion",     "#D55E00"),
    ("reddish purple", "#CC79A7"),
])

COMMUNITY_COLORS = list(COMMUNITIES.values())
COMMUNITY_NAMES = list(COMMUNITIES.keys())
MAX_COMMUNITIES = len(COMMUNITY_COLORS)

#: Communities beyond the cap, singletons, and unassigned nodes.
OTHER = "#898781"

#: Context: the "rest of the brain" behind a highlighted community, and edges.
CONTEXT_NODE = "#d8d7d1"
CONTEXT_EDGE = "#e1e0d9"

# ------------------------------------------------------------------- surfaces

SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}
PAGE = {"light": "#f9f9f7", "dark": "#0d0d0d"}

INK = {
    "light": {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7"},
    "dark":  {"primary": "#ffffff", "secondary": "#c3c2b7", "muted": "#898781",
              "grid": "#2c2c2a", "axis": "#383835"},
}

# --------------------------------------------------------------------- ramps

#: Sequential = ONE hue, light -> dark. For connectivity magnitude (matrices,
#: heatmaps). Documented blue ramp, steps 100 -> 700.
BLUE_RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
             "#0d366b"]

#: Second sequential context, when two must appear at once (orange hue).
ORANGE_RAMP = ["#fbe3d3", "#f7c6a8", "#f3a97d", "#ef8c52", "#eb6834",
               "#d95926", "#b8481e", "#963916", "#742b10"]

#: Diverging = two hues + NEUTRAL GREY midpoint. For contrasts (e.g. within
#: minus between, or referred minus comparison). Never a hue at the midpoint.
DIVERGING_NEG = "#184f95"
DIVERGING_MID = {"light": "#f0efec", "dark": "#383835"}
DIVERGING_POS = "#a8302f"


def sequential_cmap(name="calm_seq", reverse=False):
    """One-hue blue ramp for magnitude. Lightest step means near-zero."""
    stops = BLUE_RAMP[::-1] if reverse else BLUE_RAMP
    return LinearSegmentedColormap.from_list(name, stops)


def sequential_alt_cmap(name="calm_seq_alt", reverse=False):
    """Second sequential ramp, for when two magnitude scales coexist."""
    stops = ORANGE_RAMP[::-1] if reverse else ORANGE_RAMP
    return LinearSegmentedColormap.from_list(name, stops)


def diverging_cmap(name="calm_div", mode="light"):
    """Blue <-> red with a neutral grey midpoint. Equal steps per arm."""
    return LinearSegmentedColormap.from_list(
        name, [DIVERGING_NEG, "#5598e7", DIVERGING_MID[mode], "#d9736f",
               DIVERGING_POS])


def community_cmap(n=None):
    """Discrete colormap over community slots (for imshow of assignments)."""
    n = MAX_COMMUNITIES if n is None else min(n, MAX_COMMUNITIES)
    return ListedColormap(COMMUNITY_COLORS[:n], name="calm_communities")


def community_color(i, n_communities=None):
    """Colour for community index i (0-based). Past the cap -> OTHER grey.

    Identity follows the community, never its rank or size, so a filter that
    drops a community must not repaint the survivors.
    """
    if i is None or i < 0 or i >= MAX_COMMUNITIES:
        return OTHER
    if n_communities is not None and n_communities > MAX_COMMUNITIES \
            and i >= MAX_COMMUNITIES:
        return OTHER
    return COMMUNITY_COLORS[i]


def community_palette(n):
    """First n community colours, with OTHER filling anything past the cap."""
    return [community_color(i) for i in range(n)]


# ---------------------------------------------------------------- typography

#: Lato is installed system-wide on the CBU cluster and is the project face.
#: The fallbacks are metric-compatible enough to keep layout stable elsewhere.
FONT_STACK = ["Lato", "Liberation Sans", "DejaVu Sans", "sans-serif"]

#: Type scale, in points, for figures authored at 180 mm width.
TYPE = {
    "figure_title": 11.0,
    "panel_title": 9.5,
    "axis_label": 8.5,
    "tick": 7.5,
    "annotation": 7.5,
    "legend": 8.0,
    "caption": 7.0,
}

# ------------------------------------------------------------------ the style


def rc(mode="light"):
    """Return the rcParams dict for a mode (does not apply it)."""
    ink = INK[mode]
    return {
        "figure.facecolor": SURFACE[mode],
        "figure.edgecolor": SURFACE[mode],
        "figure.dpi": 150,
        "savefig.dpi": 400,
        "savefig.facecolor": SURFACE[mode],
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "savefig.transparent": False,

        "axes.facecolor": SURFACE[mode],
        "axes.edgecolor": ink["axis"],
        "axes.labelcolor": ink["secondary"],
        "axes.titlecolor": ink["primary"],
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.axisbelow": True,
        "axes.titlesize": TYPE["panel_title"],
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 6.0,
        "axes.labelsize": TYPE["axis_label"],
        "axes.prop_cycle": mpl.cycler(color=COMMUNITY_COLORS),

        "grid.color": ink["grid"],
        "grid.linewidth": 0.5,

        "xtick.color": ink["muted"],
        "ytick.color": ink["muted"],
        "xtick.labelcolor": ink["secondary"],
        "ytick.labelcolor": ink["secondary"],
        "xtick.labelsize": TYPE["tick"],
        "ytick.labelsize": TYPE["tick"],
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.direction": "out",
        "ytick.direction": "out",

        "font.family": "sans-serif",
        "font.sans-serif": FONT_STACK,
        "font.size": TYPE["axis_label"],
        "text.color": ink["primary"],

        "legend.frameon": False,
        "legend.fontsize": TYPE["legend"],
        "legend.handlelength": 1.1,
        "legend.handleheight": 1.1,
        "legend.borderpad": 0.0,
        "legend.labelspacing": 0.5,
        "legend.columnspacing": 1.2,

        "lines.linewidth": 2.0,       # 2px lines
        "lines.markersize": 4.0,      # >= 8px diameter
        "lines.solid_capstyle": "round",

        "patch.linewidth": 0.0,
        "image.cmap": "calm_seq",
        "image.interpolation": "nearest",

        "pdf.fonttype": 42,           # embed real text, not paths
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }


_REGISTERED = False


def _register_cmaps():
    global _REGISTERED
    if _REGISTERED:
        return
    for cm in (sequential_cmap(), sequential_alt_cmap(), diverging_cmap(),
               community_cmap()):
        try:
            mpl.colormaps.register(cm, force=True)
        except Exception:
            pass
    for cm in (sequential_cmap("calm_seq_r", reverse=True),):
        try:
            mpl.colormaps.register(cm, force=True)
        except Exception:
            pass
    _REGISTERED = True


def use_style(mode="light"):
    """Apply the project style. Call once at the top of a figure script."""
    if mode not in SURFACE:
        raise ValueError(f"mode must be 'light' or 'dark', got {mode!r}")
    _register_cmaps()
    mpl.rcParams.update(rc(mode))
    return mode


# ------------------------------------------------------------------- helpers

def finish(ax, title=None, subtitle=None, mode="light", grid=None):
    """Apply the project's title/subtitle convention and recessive chrome.

    grid: None (leave), 'x', 'y' or 'both' -- hairline, always behind the data.
    """
    ink = INK[mode]
    if title:
        ax.set_title(title, fontsize=TYPE["panel_title"], weight="semibold",
                     color=ink["primary"], loc="left", pad=14 if subtitle else 6)
    if subtitle:
        ax.annotate(subtitle, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=TYPE["annotation"], color=ink["secondary"],
                    ha="left", va="bottom")
    if grid:
        ax.grid(True, axis="both" if grid == "both" else grid,
                color=ink["grid"], linewidth=0.5)
        ax.set_axisbelow(True)
    return ax


def community_legend(ax, labels=None, n=None, mode="light", **kwargs):
    """A legend is ALWAYS present when >= 2 communities are shown.

    Identity must never rest on colour alone -- this is the secondary encoding
    the CVD floor-band obliges.
    """
    from matplotlib.lines import Line2D
    n = MAX_COMMUNITIES if n is None else n
    labels = labels or [f"Community {i + 1}" for i in range(n)]
    handles = [Line2D([], [], marker="o", linestyle="none", markersize=6,
                      markerfacecolor=community_color(i),
                      markeredgecolor=SURFACE[mode], markeredgewidth=0.8,
                      label=labels[i]) for i in range(n)]
    kwargs.setdefault("loc", "upper left")
    kwargs.setdefault("ncol", 1)
    return ax.legend(handles=handles, **kwargs)


def order_by_community(assignments):
    """Index order that groups nodes by community, plus block boundaries.

    Returns (order, boundaries, sizes). Use the SAME order in every matrix
    figure so blocks stay comparable across panels.
    """
    import numpy as np
    assignments = np.asarray(assignments)
    order = np.argsort(assignments, kind="stable")
    sorted_a = assignments[order]
    boundaries = np.flatnonzero(np.diff(sorted_a)) + 1
    _, sizes = np.unique(sorted_a, return_counts=True)
    return order, boundaries, sizes


def draw_community_blocks(ax, boundaries, n_nodes, mode="light", lw=0.9):
    """Draw community block boundaries on a reordered matrix."""
    ink = INK[mode]
    for b in boundaries:
        ax.axhline(b - 0.5, color=ink["primary"], linewidth=lw, alpha=0.55)
        ax.axvline(b - 0.5, color=ink["primary"], linewidth=lw, alpha=0.55)
    ax.set_xlim(-0.5, n_nodes - 0.5)
    ax.set_ylim(n_nodes - 0.5, -0.5)


def community_colorbars(ax, assignments, order, mode="light", width=0.022):
    """Colour bars along the top and left edges of a reordered matrix.

    This is the secondary encoding that makes the matrix readable without
    relying on the reader resolving six hues against each other.
    """
    import numpy as np
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Rectangle

    a = np.asarray(assignments)[order]
    n = len(a)
    span = width * n
    top, left = [], []
    colors = []
    for i, c in enumerate(a):
        colors.append(community_color(int(c)))
        top.append(Rectangle((i - 0.5, -0.5 - span), 1, span))
        left.append(Rectangle((-0.5 - span, i - 0.5), span, 1))
    for patches in (top, left):
        pc = PatchCollection(patches, facecolors=colors, edgecolors="none")
        pc.set_clip_on(False)
        ax.add_collection(pc)
    ax.set_xlim(-0.5 - span, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5 - span)


#: Validation record -- regenerate with scripts/validate_style.sh
VALIDATION = {
    "palette": COMMUNITY_COLORS,
    "pairs": "all",
    "light": {"cvd_dE": 7.6, "normal_dE": 15.6, "verdict": "PASS (CVD in 6-8 "
              "floor band -> secondary encoding mandatory)"},
    "dark": {"cvd_dE": 7.6, "normal_dE": 15.6, "contrast": ">=3:1 all six",
             "note": "same hexes as light, by design"},
    "sub_3to1_on_white": {"#E69F00": 2.19, "#56B4E9": 2.25, "#CC79A7": 2.98},
}
