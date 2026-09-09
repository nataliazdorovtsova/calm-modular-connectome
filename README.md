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

### Figure 4 — Modular brain architecture

*What it shows.* Three panels building one argument. **A**: the region-level
connectome collapsed into a 5 × 5 community × community matrix of mean
streamline count, with the diagonal carrying within-community connectivity.
**B**: the edge-weight distribution behind each of those block means, because a
mean over heavily skewed counts hides most of what is going on. **C**: the same
within-versus-between comparison held at matched edge length.

*How it was made.* Block means are taken over all region pairs in each block;
for diagonal blocks only the upper triangle is used, so a region is never paired
with itself. Panel A uses a logarithmic colour scale — block means span 3 to
1,540 streamlines, and a linear scale would collapse everything but the
diagonal. Panel B plots log-scaled distributions with medians marked. Panel C
bins every edge by Euclidean distance between region centroids and compares
within- against between-community means inside each bin.

*Statistics.* The proposal invites several candidate summary measures, and they
disagree sharply on these data:

| measure | within | between | ratio |
|---|---|---|---|
| mean count | 430 | 43 | 10.1× |
| median count | 57 | 0.2 | 364× |
| proportion nonzero | 0.94 | 0.55 | 1.7× |
| proportion above global 75th pct | 0.59 | 0.15 | 3.9× |
| mean log(1 + count) | 3.94 | 1.21 | 3.2× |

The median is rejected: the between-community median is essentially zero, so
its ratio is an artefact of a near-zero denominator rather than a finding. The
mean is used in panel A because it is interpretable in streamlines, with panel B
supplying the spread it conceals.

Panel C addresses a confound that Figure 3 creates. Those communities are
spatially compact, within-community edges are shorter than between-community
ones (**58 vs 87 mm**), and streamline count falls steeply with distance
(**r = −0.47**) — so "10× more connectivity within communities" risks being a
restatement of "within-community edges are shorter". Comparing like with like
inside distance bins, the gap not only survives but **widens with distance**:
2.5× at 0–30 mm, 3.2× at 30–50, 4.0× at 50–70, 7.0× at 70–90 and 10.5× beyond
90 mm. Modular structure here is therefore not a distance artefact.

### Figure 5 — The connectome collapsed

*What it shows.* Four frames of a single transformation, left to right: the
region-level connectome in anatomical space, two intermediate states, and the
community-level network. Every frame is the same data; only the geometry
changes.

*How it was made.* Each region's position is linearly interpolated from its true
MNI coordinate toward its own community's centroid,

    position(t) = (1 − t) × anatomical + t × community centroid

so t = 0 reproduces Figure 1 and at t = 1 every region of a community sits at
one point — at which the connectome *is* the community graph. Three things are
tied to t so the row reads as one motion rather than four unrelated pictures:

- **the glass-brain outline fades out**, because after t = 0 the positions are
  no longer anatomical and keeping a brain frame around them would be a lie;
- **within-community edges fade out**, since a collapsing community absorbs its
  own internal connections;
- **between-community edges keep their endpoints**, so as communities converge
  these edges pile onto the same segments. The super-edges in the final panel
  therefore assemble themselves out of region-level edges by superposition —
  the figure shows where community-level connectivity *comes from* rather than
  asserting it.

Super-node radius is set from the geometry rather than by eye: the two closest
community centroids in this plane are 24 mm apart, so radii are capped at 40% of
that separation, with area kept proportional to region count inside the ceiling.
Without that constraint the final panel becomes a pile of overlapping discs.

The final panel keeps the communities at their anatomical centroids, which is
what makes the sequence a *collapse* rather than a re-layout. Figure 6 takes the
same community graph into abstract space.

*Statistics.* None new — this figure re-renders the geometry of data already
quantified in Figures 1–4. Edge widths in the final panel come from the same
community × community block means shown in Figure 4A.

### Figure 6 — The network of networks

*What it shows.* A circular connectogram. All 100 regions sit on the ring,
ordered by community and then by anatomical network, each individually
labelled. The coloured arcs outside the ring are the communities — the "nodes"
of the network of networks — and the chords crossing the interior are their
relationships.

*How it was made.* Only **between-community** connections are drawn: the
previous five figures were about within-community density, and including it here
would fill the disc with structure already established. What remains is the
higher-level organisation, and specifically *which regions* carry traffic
between which communities. The 70 strongest between-community edges are shown,
as cubic Bézier chords bowed toward the centre, with curvature scaled by
angular separation so long chords do not crowd the ring.

As in Figure 5, the aggregate assembles itself: chords are drawn per region
pair, not per community pair, so a thick visual bundle between two arcs *is* the
community-level relationship, and a sparse bundle is a real absence rather than
a thresholding artefact.

Schaefer 17-network names are too long to ring a circle, so they are abbreviated
(`LH_VisCent_ExStr_1` → `L Vis-C ExStr 1`) while keeping hemisphere, network,
sub-region and index. Region labels wear ink colours rather than community
colours, per the style guide — the coloured tick beside each label carries
identity.

Chords are grey, not community-coloured, deliberately: a chord has two community
endpoints, so painting it one community's colour would claim an identity it does
not have. The palette stays on the arcs, where identity is unambiguous, and the
chord spends its width on magnitude instead.

*Statistics.* None new. The chord counts do quantify the higher-level structure:
of the 70 strongest between-community connections, community pairs 1–4 (14
chords), 2–4 (12), 3–4 (10) and 3–5 (10) dominate, while **communities 1 and 2 —
the wholly left and wholly right communities — take only 1 chord between them**.
That is the corpus callosum bottleneck appearing as a near-absence, and it is
consistent with their block mean of 3 streamlines in Figure 4A against 284 and
479 within.

---

## Beyond the six

### Figure 7 — Networks versus communities

*What it shows.* The Schaefer parcellation ships an a priori functional
partition — the canonical Yeo networks, 16 of which appear in the 100-region
atlas. The five communities in Figures 1–6 were derived from the structural data
itself. This figure asks whether they agree. **A**: the 16 × 16 network × network
connectivity matrix. **B**: modularity Q of four candidate partitions on the same
connectome. **C**: how the five communities distribute across the 16 networks.

*How it was made.* Network block means follow the same convention as Figure 4A
(diagonal blocks use the upper triangle only), on a logarithmic colour scale.
Panel A is deliberately left in canonical Yeo order rather than reordered to
look blocky: Figure 2 could reorder because the point there was that blocks
exist, whereas here the point is that they largely do not, and permuting until
they appeared would manufacture the opposite conclusion.

*Statistics.* Newman modularity Q is computed for each candidate partition on
the identical weighted graph, so the numbers are directly comparable:

| partition | Q |
|---|---|
| Louvain communities (5) | **0.528** |
| Hemisphere (2) | 0.271 |
| Schaefer networks (16) | **0.158** |
| Networks × hemisphere (32) | 0.078 |

Agreement between partitions is measured with adjusted mutual information, which
corrects for the chance agreement expected from partition sizes alone:
**AMI = 0.16** between communities and networks, against **AMI = 0.36** between
communities and hemisphere.

The a priori functional networks therefore describe this structural connectome
*worse than simply splitting the brain in half*, and the data-driven communities
align more than twice as strongly with hemisphere as with functional network.
Structural modules here follow space, not function. This is consistent with what
Figures 1 and 3 show anatomically, and it is a property of streamline-count
tractography rather than a claim about functional organisation.

### Figure 8 — The functional networks

*What it shows.* Where the 16 Schaefer networks sit on the cortex, and how they
interconnect. **A**: one small brain per network, in canonical Yeo order so
families read together, with that network's regions in colour against the rest
of the cortex in grey. **B**: the networks as a graph, chord width by mean
between-network connectivity and node size by region count.

*How it was made.* Two layout decisions were forced by the data rather than
chosen.

**The networks are faceted, not colour-coded.** Sixteen categories cannot be
given sixteen colourblind-safe colours — the palette caps categorical identity
at six, and no ordering beyond that clears the all-pairs gate (see
[STYLE_GUIDE.md](STYLE_GUIDE.md)). One network per panel means no two network
colours are ever compared, so the panel label carries identity and every panel
shares a single neutral accent. That accent is deliberately not one of the six
community slots, since reusing a community colour here would imply an identity
that is not being claimed.

**Panel B is circular rather than anatomical.** The first version placed each
network at its own centroid on a glass brain. Because most networks are
bilateral, their centroids average to near the midline, and the axial view
stacked them into an unreadable column with labels too large for their nodes.
Panel A already carries the anatomy, so freeing panel B from it lets position
serve legibility instead.

*Statistics.* None new; block means follow the same convention as Figures 4A and
7A. The strongest between-network pairs are Cont-A–Cont-B (547 streamlines),
dAttn-A–Cont-B (396) and Limbic–Def-C (376) — note these are pairs of
*neighbouring* networks, consistent with the distance dependence quantified in
Figure 4C.

---

## Notes

See [CONTRIBUTING.md](CONTRIBUTING.md) before making a figure or a commit.

The analysis data is not in this repository and is not redistributable.
