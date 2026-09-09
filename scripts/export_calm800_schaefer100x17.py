#!/usr/bin/env python
"""
Export CALM 800 (referred) connectomes, Schaefer 100 x17 parcellation, to CSV.

Source : the qsiprep CALM .mat (MATLAB v7.3 / HDF5); path in local_paths.py
Subset : the 315 subjects whose CALM ID appears in the CALM 800 datasheet
         (verified identical to the sample.control == 0 "referred" flag)
Edges  : datatype MATLAB index 1 (= HDF5 index 0), integer streamline counts

Two caveats, both load-bearing.

1. The source file stores `info.datatypes` as an EMPTY MATLAB placeholder, in
   every copy on the system -- the 8 datatypes are genuinely unlabelled. Index 1
   was identified as streamline count empirically (integer-valued, 16.4% edge
   density) and matches the datatype used by the existing lab script
   ge02/connectomes.m. If you switch DATATYPE, confirm what the new index is
   first; nothing on disk records it.

2. These counts are RAW -- not harmonised, not thresholded, not normalised for
   head size or streamline total. Harmonised and thresholded CALM connectomes do
   exist elsewhere on the cluster, but both are Schaefer x7 only, so neither is
   a drop-in substitute for this x17 export.

Note on axis order. The .mat stores parcellated data as
    subject x datatype x node x node
h5py reverses HDF5 dimensions, so the array reads as
    (node, node, datatype, subject)
and conn[:, :, 0, s] is the 100x100 matrix for subject s. The matrices are
symmetric with a zero diagonal, so the reversal does not transpose anything
meaningful, but the ordering is asserted below rather than assumed.

Run:
  env/bin/python scripts/export_calm800_schaefer100x17.py
"""

import csv
import os
import sys

import h5py
import numpy as np

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)
try:
    from local_paths import SOURCE_MAT as MAT, DATASHEET
except ImportError:                                    # pragma: no cover
    raise SystemExit(
        "Missing local_paths.py -- it holds the cluster paths to the raw data "
        "and is deliberately not in the repository.\n"
        "  cp local_paths.example.py local_paths.py   # then edit it")
OUT = os.path.join(PROJ, "data")

PARC = "schaefer100x17"
DATATYPE = 0          # HDF5 index; MATLAB index 1 = streamline count
ID_COL = "ID No."


def hdf5_strings(h, dataset):
    """Decode a MATLAB cell-array-of-char stored as HDF5 object references."""
    out = []
    for ref in np.array(dataset).flatten():
        chars = np.array(h[ref]).flatten()
        out.append("".join(chr(int(c)) for c in chars).strip())
    return out


def datasheet_ids(path):
    """CALM IDs present in the CALM 800 datasheet."""
    ids = set()
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get(ID_COL) or "").strip()
            try:
                ids.add(int(float(raw)))
            except ValueError:
                pass
    return ids


def main():
    conn_dir = os.path.join(OUT, "connectomes_schaefer100x17_count")
    os.makedirs(conn_dir, exist_ok=True)

    h = h5py.File(MAT, "r")
    g = h["calm_qsiprep"]
    sample = g["sample"]

    calm_id = np.array(sample["id"]["calm"]).flatten()
    control = np.array(sample["control"]).flatten()
    age_scan = np.array(sample["age"]["scan"]).flatten()
    age_test = hdf5_strings(h, sample["age"]["test"])
    sex = hdf5_strings(h, sample["sex"])

    conn = g[PARC]["connectivity"]
    n_sub = calm_id.size
    assert conn.shape == (100, 100, 8, n_sub), f"unexpected shape {conn.shape}"

    # --- select the CALM 800 subset -------------------------------------
    in800 = np.array([int(x) in datasheet_ids(DATASHEET) for x in calm_id])
    assert np.array_equal(in800, control == 0), \
        "CALM 800 membership no longer matches the referred flag"
    idx = np.flatnonzero(in800)
    print(f"selected {idx.size} CALM 800 subjects of {n_sub}")

    # --- region labels and coordinates ----------------------------------
    labels = hdf5_strings(h, g[PARC]["regionlabels"])
    coords = np.array(g[PARC]["coordinates"])          # (3, 100)
    assert len(labels) == 100 and coords.shape == (3, 100)

    with open(os.path.join(OUT, "region_labels_schaefer100x17.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["region_index", "region_label", "x", "y", "z"])
        for i, lab in enumerate(labels):
            w.writerow([i + 1, lab, *(f"{v:g}" for v in coords[:, i])])

    # --- per-subject matrices -------------------------------------------
    header = [""] + labels
    written = []
    for s in idx:
        m = conn[:, :, DATATYPE, s]
        assert np.allclose(m, m.T), f"subject index {s} matrix not symmetric"
        sid = int(calm_id[s])
        path = os.path.join(conn_dir, f"sub-{sid}.csv")
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            for i, lab in enumerate(labels):
                w.writerow([lab] + [f"{v:g}" for v in m[i]])
        written.append((sid, s, m))

    print(f"wrote {len(written)} matrices to {conn_dir}")

    # --- phenotype ------------------------------------------------------
    with open(os.path.join(OUT, "phenotype_calm800.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["calm_id", "connectome_file", "age_at_scan_years",
                    "age_at_test", "sex", "sex_label", "control",
                    "n_edges_nonzero", "density", "total_streamlines"])
        for sid, s, m in written:
            iu = np.triu_indices(100, 1)
            edges = m[iu]
            sx = sex[s]
            w.writerow([
                sid, f"sub-{sid}.csv", f"{age_scan[s]:.3f}", age_test[s], sx,
                {"1": "male", "2": "female"}.get(sx, "unknown"),
                int(control[s]), int((edges != 0).sum()),
                f"{(edges != 0).mean():.4f}", int(edges.sum()),
            ])

    # --- matched slice of the CALM 800 datasheet ------------------------
    keep = {sid for sid, _, _ in written}
    with open(DATASHEET, newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            raw = (row.get(ID_COL) or "").strip()
            try:
                if int(float(raw)) in keep:
                    rows.append(row)
            except ValueError:
                pass
        fields = reader.fieldnames
    out_ds = os.path.join(OUT, "calm800_datasheet_matched.csv")
    with open(out_ds, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"matched datasheet rows: {len(rows)} -> {out_ds}")

    h.close()


if __name__ == "__main__":
    main()
