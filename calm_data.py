"""
Shared data access for every figure in the project.

The point of this module is CONSISTENCY. The proposal requires that a reader can
track a community across all six figures, which only works if every figure uses
the same connectome, the same community assignments and the same slot order.
So communities are detected ONCE, cached to disk, and loaded thereafter --
never recomputed per figure (Louvain is stochastic; recomputing would silently
reshuffle identities between figures).

    import sys, os; sys.path.insert(0, os.path.dirname(__file__))
    import calm_data as cd

    W      = cd.group_average()      # 100x100 mean connectome, CALM 800
    assign = cd.communities()        # community slot per region (0-based)
    coords = cd.coordinates()        # 100x3 MNI mm
    labels = cd.region_labels()      # Schaefer 100x17 names
"""

import os
import numpy as np

PROJ = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(PROJ, "data")
CONN = os.path.join(DATA, "connectomes_schaefer100x17_count")
GROUP_AVG = os.path.join(DATA, "group_average_schaefer100x17.csv")
COMMUNITIES = os.path.join(DATA, "community_assignments_groupavg.csv")
LABELS = os.path.join(DATA, "region_labels_schaefer100x17.csv")

N_REGIONS = 100
SEED = 0

_cache = {}


def group_average(force=False):
    """Mean connectome over the 315 CALM 800 subjects (cached to disk)."""
    if "W" in _cache and not force:
        return _cache["W"]
    if os.path.exists(GROUP_AVG) and not force:
        W = np.loadtxt(GROUP_AVG, delimiter=",")
    else:
        import glob
        files = sorted(glob.glob(os.path.join(CONN, "sub-*.csv")))
        if not files:
            raise FileNotFoundError(
                f"No connectomes in {CONN}. Run:\n"
                f"  env/bin/python scripts/export_calm800_schaefer100x17.py")
        tot = None
        for f in files:
            m = np.loadtxt(f, delimiter=",", skiprows=1,
                           usecols=range(1, N_REGIONS + 1), dtype=float)
            tot = m if tot is None else tot + m
        W = tot / len(files)
        np.savetxt(GROUP_AVG, W, delimiter=",", fmt="%.6f")
    assert W.shape == (N_REGIONS, N_REGIONS)
    assert np.allclose(W, W.T), "group average must be symmetric"
    _cache["W"] = W
    return W


def communities(force=False):
    """Community slot per region. Detected once, then loaded from disk.

    Louvain is stochastic, so this is cached deliberately: every figure must
    show the SAME communities in the SAME colours, or the visual narrative
    breaks. Delete the cache file to re-detect.
    """
    if "assign" in _cache and not force:
        return _cache["assign"]
    if os.path.exists(COMMUNITIES) and not force:
        a = np.loadtxt(COMMUNITIES, delimiter=",", skiprows=1,
                       usecols=1).astype(int)
    else:
        import networkx as nx
        W = group_average()
        G = nx.from_numpy_array(W)
        comms = nx.community.louvain_communities(G, weight="weight", seed=SEED,
                                                 resolution=1.0)
        comms = sorted(comms, key=len, reverse=True)   # largest = slot 0
        a = np.full(N_REGIONS, 6, dtype=int)           # 6 = OTHER
        for k, nodes in enumerate(comms):
            for nd in nodes:
                a[nd] = k if k < 6 else 6
        np.savetxt(COMMUNITIES, np.c_[np.arange(1, N_REGIONS + 1), a],
                   delimiter=",", fmt="%d",
                   header="region_index,community_slot", comments="")
    _cache["assign"] = a
    return a


def _labels_table():
    if "labels" in _cache:
        return _cache["labels"]
    names, coords = [], []
    with open(LABELS) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split(",")
            names.append(p[1])
            coords.append([float(p[2]), float(p[3]), float(p[4])])
    _cache["labels"] = (names, np.array(coords))
    return _cache["labels"]


def region_labels():
    return _labels_table()[0]


def coordinates():
    """100 x 3 MNI coordinates (mm)."""
    return _labels_table()[1]


def community_sizes(assign=None):
    assign = communities() if assign is None else assign
    return {k: int((assign == k).sum()) for k in sorted(set(assign.tolist()))}


def present_communities(assign=None):
    """Community slots actually present, in slot order."""
    assign = communities() if assign is None else assign
    return sorted(set(assign.tolist()))


def modularity(W=None, assign=None):
    """Newman modularity Q of the cached partition."""
    import networkx as nx
    W = group_average() if W is None else W
    assign = communities() if assign is None else assign
    G = nx.from_numpy_array(W)
    parts = [set(np.flatnonzero(assign == k).tolist())
             for k in present_communities(assign)]
    return nx.community.modularity(G, parts, weight="weight")


def network_labels(assign=None):
    """Descriptive name per community, from its dominant Schaefer network.

    Schaefer region names look like 'LH_VisCent_ExStr_1' -- the second field is
    the network. Naming communities by their dominant network makes the legend
    interpretable instead of 'Community 1..5'.
    """
    from collections import Counter
    assign = communities() if assign is None else assign
    names = region_labels()
    out = {}
    for k in present_communities(assign):
        nets = [names[i].split("_")[1] for i in np.flatnonzero(assign == k)
                if len(names[i].split("_")) > 1]
        c = Counter(nets).most_common()
        top, n = c[0]
        out[k] = (top, n / max(1, len(nets)))
    return out


def summary():
    W, a = group_average(), communities()
    print(f"  connectome     : {W.shape}, mean edge {W[W > 0].mean():.1f}")
    print(f"  communities    : {len(present_communities(a))}  sizes {community_sizes(a)}")
    print(f"  modularity Q   : {modularity():.3f}")
    for k, (net, frac) in network_labels().items():
        print(f"    slot {k+1}: dominant network {net} ({frac:.0%})")


if __name__ == "__main__":
    summary()
