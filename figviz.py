"""
Shared plotting plumbing for the brain-rendering figures.

Kept separate from calm_style (which owns the visual language) and calm_data
(which owns the numbers). This module only knows how to get nodes and edges
onto a nilearn glass brain in the right place.
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")
import numpy as np
from matplotlib.collections import LineCollection
from nilearn import plotting

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style import calm_style as cs   # noqa: E402

#: nilearn draws each view in MNI millimetres, so a projection is just a choice
#: of which two coordinates to plot. Verified against the axes limits nilearn
#: sets ('l' and 'r' share the sagittal plane but mirror the anterior axis).
_PLANES = {"l": (1, 2), "r": (1, 2), "x": (1, 2),   # sagittal: (y, z)
           "y": (0, 2),                             # coronal:  (x, z)
           "z": (0, 1)}                             # axial:    (x, y)


def project(coords, direction):
    """MNI mm (n x 3) -> the 2-D plane nilearn draws for `direction`."""
    try:
        a, b = _PLANES[direction]
    except KeyError:
        raise ValueError(f"unknown view {direction!r}; expected one of "
                         f"{sorted(_PLANES)}")
    return np.c_[coords[:, a], coords[:, b]]


def glass_panel(ax, direction, alpha=0.10):
    """Draw an empty glass brain into `ax`; return the axes to plot onto."""
    display = plotting.plot_glass_brain(
        None, display_mode=direction, axes=ax, annotate=False,
        black_bg=False, alpha=alpha)
    return display.axes[direction].ax


def hemisphere_mask(coords, direction):
    """True for nodes belonging in a sagittal panel; all True otherwise.

    Projecting both hemispheres onto one sagittal plane superimposes different
    communities and hides lateralisation, so sagittal views take one side only.
    """
    if direction == "l":
        return coords[:, 0] < 0
    if direction == "r":
        return coords[:, 0] >= 0
    return np.ones(len(coords), dtype=bool)


def draw_edges(pax, P, pairs, assign, show=None, within_lw=0.85,
               between_lw=0.45, within_alpha=0.55, only_within=False):
    """Edges, split so within-community ones carry their community colour.

    `pairs` is (i_array, j_array). Between-community edges are drawn first and
    recessive; within-community edges sit on top in colour, so modular
    structure reads directly off the picture.
    """
    show = np.ones(len(P), dtype=bool) if show is None else show
    within, wcol, between = [], [], []
    for i, j in zip(*pairs):
        if not (show[i] and show[j]):
            continue
        seg = [P[i], P[j]]
        if assign[i] == assign[j]:
            within.append(seg)
            wcol.append(cs.community_color(int(assign[i])))
        elif not only_within:
            between.append(seg)
    if between:
        pax.add_collection(LineCollection(
            between, colors=cs.CONTEXT_EDGE, linewidths=between_lw,
            alpha=0.85, zorder=2, capstyle="round"))
    if within:
        pax.add_collection(LineCollection(
            within, colors=wcol, linewidths=within_lw, alpha=within_alpha,
            zorder=3, capstyle="round"))
    return len(within), len(between)


def draw_nodes(pax, P, assign, sizes, show=None, mode="light", ring=0.7,
               zorder=4, color_override=None):
    """Community-coloured nodes with a surface-coloured ring, hubs on top."""
    show = np.ones(len(P), dtype=bool) if show is None else show
    idx = np.flatnonzero(show)
    if idx.size == 0:
        return
    s = np.asarray(sizes)
    idx = idx[np.argsort(s[idx])]
    colors = ([color_override] * len(idx) if color_override is not None
              else [cs.community_color(int(assign[i])) for i in idx])
    pax.scatter(P[idx, 0], P[idx, 1], s=s[idx], c=colors,
                edgecolors=cs.SURFACE[mode], linewidths=ring, zorder=zorder)


def top_edges(W, pct):
    """Indices of the strongest `100 - pct`% of edges, upper triangle only."""
    iu = np.triu_indices_from(W, 1)
    thr = np.percentile(W[iu], pct)
    keep = W[iu] >= thr
    return (iu[0][keep], iu[1][keep]), thr, int(keep.sum()), len(iu[0])
