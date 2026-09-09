# CALM modular connectome visualisation

An internship project by Sabrina E Harverson at the University of Cambridge CMBI.

A one-week exploratory project: a visual atlas of modular organisation in the
CALM structural connectomes.

**Regions → Communities → Community interactions → Network of networks**

---

## Shared method

Everything below rests on the same three choices, so the figures are directly
comparable to one another.

**The connectome.** A group-average structural connectome: the mean of 315
individual matrices, parcellated with Schaefer 100×17 (100 cortical regions,
17-network solution). Edge weights are streamline counts from probabilistic
tractography. Counts are raw — not harmonised, thresholded, or corrected for
distance or head size.

**The communities.** Detected once with the Louvain algorithm (weighted,
resolution 1.0, fixed random seed) on the group-average matrix, which yields
**five communities** with **modularity Q = 0.53**. The partition is cached to
disk and every figure loads that same cached result. This matters: Louvain is
stochastic, so re-running it per figure would silently reshuffle which regions
belong to which community, and a reader could no longer follow a community from
one figure to the next.

**The colours.** One fixed palette (Okabe-Ito), assigned by slot, used
identically in every figure. Community 3 is the same green everywhere. See
[STYLE_GUIDE.md](STYLE_GUIDE.md) for why that palette and not another.

---

## Figures

### Figure 1 — The modular connectome

*What it shows.* The whole-brain network in anatomical space, in four
projections (left and right sagittal, coronal, axial). Each region is a node
coloured by its community; node size is weighted degree, so hubs are visible
without spending the colour channel on magnitude.

*How it was made.* Nodes are placed at their MNI centroids on a glass-brain
outline. Drawing all 4,950 edges is unreadable, so only the strongest 3% (149
edges) are shown; within-community edges take their community's colour and
between-community edges are muted grey, which makes modularity legible directly
from the picture — 119 of the 149 drawn edges are within-community. The sagittal
panels are restricted to their own hemisphere, because projecting both sides
onto one plane superimposes different communities and hides lateralisation.

*Statistics.* Newman modularity Q = 0.53 for the cached partition.

### Figure 2 — Communities in connectivity space

*What it shows.* The 100 × 100 region-by-region connectivity matrix under two
orderings: the Schaefer atlas order (hemisphere, then network) and the community
order. Community identity runs along both edges of the right panel as colour
bars, with block boundaries and numbered diagonal blocks.

*How it was made.* Two panels rather than one, deliberately: a community-ordered
matrix alone begs the question, since any matrix can be made to look blocky if
you are free to permute it. The panels differ *only* by a permutation of rows
and columns and share an identical colour scale, so the block structure is a
property of the data rather than of the rendering. Colour is log(1 + streamline
count) — the raw counts are heavily right-skewed, so a linear scale would show
almost nothing — with the scale capped at the 99.5th percentile so a few very
strong edges do not flatten everything else.

*Statistics.* Mean connectivity computed on the raw counts: **430 streamlines
within community versus 43 between, a 10.1× ratio.**

### Figure 3 — Communities in anatomical space

*What it shows.* One column per community: that community's regions in colour
against the rest of the brain in muted grey, in axial and sagittal views, with
only its own internal connections drawn. Faceting means no two community
colours are ever compared side by side, which is also what the palette's
colourblind-safety margin requires.

*How it was made.* Same node placement as Figure 1, with the strongest 10% of
within-community edges shown (a community's internal edges are sparser than the
whole-brain set, so a more permissive threshold is appropriate). Region counts
and left/right composition are reported per community.

*Statistics.* The proposal asks whether communities are compact, distributed or
spatially heterogeneous, so this is measured rather than judged by eye. Spatial
dispersion is the mean Euclidean distance (mm) of a community's regions from
their own centroid. Each observed value is compared against a **permutation
null of 20,000 random region sets of matched size**, drawn from the same 100
coordinates; the reported p is the proportion of null draws at least as compact
as the observed value. **All five communities are significantly more spatially
compact than chance** (25–44 mm observed against 55–58 mm expected; p ≤ 0.001),
so the partition tracks anatomy closely rather than being spatially diffuse.

---

## Notes

See [CONTRIBUTING.md](CONTRIBUTING.md) before making a figure or a commit.

The analysis data is not in this repository and is not redistributable.
