# Contributing

## 1. The data rule — read this first

**No participant data goes in this repository. Ever.**

`data/` is gitignored and stays on the CBU imaging space. It contains
per-subject CALM connectomes keyed by participant ID, and a behavioural
datasheet carrying special-category health data under UK GDPR. Committing any
of it would move CALM data off CBU-controlled infrastructure and outside its
governance framework.

Nothing is lost by this: the whole of `data/` is regenerable in one command by
anyone with cluster access (see below).

Practical rules:

- Never `git add -f` anything under `data/`.
- Never paste participant-level numbers, CALM IDs, or datasheet rows into
  commit messages, issues, or pull requests.
- Figures showing **group-level** results (a group-average matrix, community
  structure over all 315) are aggregate and fine. A figure showing a **single
  identifiable participant** is not — keep it in `data/` or `figures/private/`.
- If you are unsure whether something is shareable, ask Natalia before
  committing. Ask first; a bad commit lives in the history forever.

## 2. Getting set up

You need an MRC CBU cluster account with access to the CALM data. The repo
alone is not enough to run anything — the data lives on the cluster.

```bash
cd <project root>

# one-off: build the environment (~1.7 GB, a few minutes)
bash scripts/setup_env.sh

# point the code at the raw data (these paths are not in the repo)
cp local_paths.example.py local_paths.py   # then edit it

# regenerate data/ from the source .mat
env/bin/python scripts/export_calm800_schaefer100x17.py

# check it all works
env/bin/python scripts/make_style_guide.py
```

Use `env/bin/python` directly — no activation needed. For notebooks:
`env/bin/jupyter lab`.

## 3. Before you make a figure

Read [STYLE_GUIDE.md](STYLE_GUIDE.md). Every figure starts with:

```python
import sys; sys.path.insert(0, "<project root>")
from style import calm_style as cs
cs.use_style()
```

The two rules that are easiest to break by accident:

- **Community colour follows the community, never its rank.** Community 3 is
  bluish green in every figure. If a filter drops a community, the survivors
  keep their colours.
- **Six communities is a cap.** A seventh folds into `OTHER` grey or gets its
  own facet — do not invent a seventh hue, it breaks the colourblind-safety
  gate. Re-check with `bash scripts/validate_style.sh` after any palette change.

## 4. Credit for pair work

Most of this project is written while pairing through Natalia's account. Git
records only one author per commit, so joint work is credited with a trailer:

```
Co-Authored-By: Sabrina Harverson <sabrina.eharverson@gmail.com>
```

GitHub renders both people on the commit, and it counts toward Sabrina's
contribution graph — provided that address is registered on her GitHub account
(**Settings → Emails**). If it is not, the trailer still records authorship
honestly but will not link to her profile.

Two ways to add it, already configured for this clone:

```bash
git pair "Figure 2: community-ordered connectivity matrix"   # one-liner
git commit                                                   # opens the template
```

`git pair` appends the trailer for you. Plain `git commit` (no `-m`) opens the
editor pre-filled from `.gitmessage` — **delete the trailer if Sabrina was not
involved.** Attribution should be accurate, not automatic. Note that
`git commit -m "..."` bypasses the template entirely, which is exactly why
`git pair` exists.

These are local settings, so they do not travel with a clone. To set them up
again elsewhere:

```bash
git config commit.template .gitmessage
git config alias.pair '!f() { git commit -m "$1" -m "Co-Authored-By: Sabrina Harverson <sabrina.eharverson@gmail.com>"; }; f'
```

Once Sabrina is pushing her own branches, her commits stand on their own and
need no trailer.

## 5. Workflow

Small, readable commits. Work on a branch and open a pull request rather than
committing to `main`:

```bash
git checkout -b figure-1-modular-connectome
# ... work ...
git add scripts/make_figure1.py figures/figure1.pdf
git commit -m "Figure 1: modular connectome in anatomical space"
git push -u origin figure-1-modular-connectome
```

Then open a PR on GitHub for review.

Keep scripts runnable end to end: someone should be able to clone, run
`setup_env.sh`, run the export, and reproduce every figure without hand-editing
paths.
