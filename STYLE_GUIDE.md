# CALM connectome figures — style guide

The rendered guide is **[figures/style_guide.pdf](figures/style_guide.pdf)**
(2 pages: the system, then the system applied to real CALM data). This file is
the rulebook behind it.

Everything is applied by one import:

```python
import sys; sys.path.insert(0, "<project root>")
from style import calm_style as cs

cs.use_style()                    # light (publication). cs.use_style("dark") for slides.
```

---

## 1. The community palette

Six slots, Okabe-Ito, in a **fixed order that never changes**:

| slot | name | hex |
|---|---|---|
| 1 | orange | `#E69F00` |
| 2 | sky blue | `#56B4E9` |
| 3 | bluish green | `#009E73` |
| 4 | blue | `#0072B2` |
| 5 | vermillion | `#D55E00` |
| 6 | reddish purple | `#CC79A7` |
| — | other / unassigned | `#898781` |

**Colour follows the community, never its rank or size.** Community 3 is bluish
green in every figure, in every panel, forever. If a filter drops a community,
the survivors keep their colours — they do not shuffle up.

### Why this palette, in numbers

Community colour here is read **all-pairs**: in a brain render any two
communities can end up adjacent, so *every* pair must separate — a much harder
gate than the adjacent-only case that governs bars and stacks. Measured
(OKLab ΔE ×100, Machado-Oliveira-Fernandes 2009 CVD simulation at severity 1.0):

| palette | worst CVD ΔE | worst normal ΔE | verdict |
|---|---|---|---|
| **Okabe-Ito 6** | **7.6** | **15.6** | **PASS** |
| Okabe-Ito 7 (+ yellow) | 7.6 | 15.6 | FAIL — yellow breaks the lightness band, 1.29:1 on white |
| Tol bright 6 | 8.3 | 18.0 | FAIL — lightness band + chroma floor |
| Tol muted 6 | 5.2 | 15.9 | FAIL — CVD |
| generic 8-hue default | — | 13.7 at 4 slots | FAIL |

A brute-force max-min search over OKLCH space scores higher (ΔE 17.2) but
returns three blues and three greens: it buys separation with lightness and
spends all the hue variety. Hue variety is exactly the channel this project
needs a reader to track across six figures, so Okabe-Ito is kept.

Re-check any change with `bash scripts/validate_style.sh`.

### Two consequences you must honour

1. **Secondary encoding is mandatory, not decorative.** ΔE 7.6 sits in the 6–8
   floor band, which is only legal alongside a non-colour cue. Every figure
   showing communities carries at least one of: block boundaries, community
   colour bars, direct labels, numbered super-nodes, or per-community facets.
   A legend is always present when two or more communities are shown.
2. **Six is a cap, not a default.** A seventh community folds into `OTHER`
   grey or gets its own facet. Do not add a seventh hue — it breaks the gate.
   Tune the community-detection resolution to land at ≤ 6, or merge the
   smallest modules. *(On the group-average CALM 800 connectome, Louvain
   returns 5 — comfortably inside the cap.)*

Three light-mode colours sit below 3:1 on white (orange 2.19, sky blue 2.25,
reddish purple 2.98). The relief rule applies: they always ship with visible
labels.

### Dark mode

Dark mode reuses the **same hexes**. All six clear 3:1 on the dark surface and
the CVD/normal-vision separations are unchanged; only the reference lightness
band objects, and that band's purpose — marks readable against the surface — is
verified directly by the contrast check. Holding the hexes fixed makes a
community's colour invariant across paper, screen and slides, which is the
point of the project. `validate_style.sh` explains the expected FAIL line.

---

## 2. Colour by job

| job | encodes | rule |
|---|---|---|
| **Categorical** | which community | the six slots above, fixed order |
| **Sequential** | connectivity magnitude | `cs.sequential_cmap()` — one hue, light→dark |
| **Diverging** | polarity (within − between, group contrasts) | `cs.diverging_cmap()` — two hues, **neutral grey** midpoint |

- Never a rainbow; never jet.
- Never a hue at the diverging midpoint.
- **Never encode magnitude with the community palette** — that channel carries
  identity only.
- One axis per chart. Two measures of different scale → two panels, never two
  y-scales.

---

## 3. Typography

**Lato**, falling back to Liberation Sans → DejaVu Sans.
Figures are authored at **180 mm** width.

| role | pt | weight |
|---|---|---|
| figure title | 11.0 | semibold |
| panel title | 9.5 | semibold |
| axis label | 8.5 | normal |
| tick / annotation | 7.5 | normal |
| caption | 7.0 | normal |

Text always wears ink tokens (`#0b0b0b` / `#52514e` / `#898781`) — **never a
community colour**. A coloured mark next to the label carries identity.

---

## 4. Marks and chrome

- 2.0 pt lines, round caps; markers ≥ 4 pt (8 px).
- 0.6 pt axes; no top or right spine.
- Hairline grid `#e1e0d9`, always behind the data; off unless it earns its place.
- A 2 px surface-coloured ring on overlapping marks (node scatter uses this).
- Prioritise clarity over completeness: threshold edges rather than drawing all
  4 950 of them. The style guide's anatomical panel shows the top 4 %.
- Context ("the rest of the brain") is `#d8d7d1` nodes and `#e1e0d9` edges —
  present, recessive, never competing with a highlighted community.

---

## 5. Export

`cs.use_style()` sets `savefig.dpi = 400`, `pdf.fonttype = 42` and
`svg.fonttype = "none"`, so **text stays live text** in PDF and SVG rather than
being converted to outlines — editable in Illustrator/Inkscape and searchable
in the final paper. Save vector (`.pdf`/`.svg`) for anything going into a
manuscript; `.png` at 400 dpi for slides and drafts.

---

## 6. Helpers worth knowing

```python
cs.community_color(k)                  # colour for community k; OTHER past the cap
cs.community_palette(n)                # first n slot colours
cs.community_legend(ax, labels, n=5)   # the mandatory legend
order, bounds, sizes = cs.order_by_community(assign)   # matrix reordering
cs.draw_community_blocks(ax, bounds, n) # block boundaries on a reordered matrix
cs.community_colorbars(ax, assign, order)  # colour bars along matrix edges
cs.finish(ax, title=..., subtitle=...)  # project title/subtitle convention
```

Use `order_by_community` once and reuse the **same order** in every matrix
figure, so blocks stay comparable panel to panel.
