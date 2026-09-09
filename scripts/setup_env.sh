#!/bin/bash
# Build the project environment for the CALM modular-connectome visualisation work.
# Everything lives inside the project folder; nothing is installed system-wide.
#
#   bash scripts/setup_env.sh
#
# Use it afterwards with the interpreter directly (no activation needed):
#   env/bin/python
# or activate:
#   source env/bin/activate
#
# Why a venv and not conda: the site conda/mamba install is misconfigured for
# this account -- it declares an ssl_verify CA bundle path that does not exist
# on this host, then fails with KeyError('pkgs_dirs'). System python3.12 plus
# pip is simpler and fully sufficient here.

set -uo pipefail

PROJ=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENVDIR=$PROJ/env
PY=$ENVDIR/bin/python

echo "=== creating venv at ./env (python $(python3 --version 2>&1 | cut -d' ' -f2)) ==="
# Debian/Ubuntu ship python3.12 without ensurepip, so bootstrap pip manually.
python3 -m venv --without-pip "$ENVDIR"
curl -sS -o "$PROJ/scripts/get-pip.py" https://bootstrap.pypa.io/get-pip.py
"$PY" "$PROJ/scripts/get-pip.py"
"$PY" -m pip install --upgrade pip setuptools wheel

# Install in groups. Groups are independent so one failure does not sink the
# rest; anything that fails is reported at the end.
FAILED=()
install () {
    echo "=== $1 ==="
    shift
    "$PY" -m pip install "$@" || FAILED+=("$*")
}

install "core scientific stack" \
    numpy scipy pandas matplotlib seaborn scikit-learn h5py openpyxl tqdm
install "neuroimaging + brain plotting" \
    nibabel nilearn templateflow netplotbrain surfplot brainspace
install "graph theory + community detection" \
    networkx python-igraph leidenalg
install "brain connectivity toolbox" bctpy
install "louvain (legacy API)" python-louvain
install "figure composition + interactive" \
    plotly kaleido pillow svgutils pycirclize
install "notebooks" jupyterlab ipykernel

echo
echo "=== import check ==="
"$PY" - <<'PYEOF'
import importlib
mods = ["numpy","scipy","pandas","matplotlib","seaborn","sklearn","nibabel",
        "nilearn","templateflow","netplotbrain","surfplot","brainspace",
        "networkx","igraph","leidenalg","bct","community","plotly",
        "pycirclize","svgutils"]
bad = []
for m in mods:
    try:
        mm = importlib.import_module(m)
        print(f"  {m:14s} {getattr(mm, '__version__', 'ok')}")
    except Exception as e:
        print(f"  {m:14s} FAIL ({type(e).__name__})")
        bad.append(m)
print("\nimport check:", "ALL OK" if not bad else f"failed: {bad}")
PYEOF

if [ ${#FAILED[@]} -ne 0 ]; then
    echo
    echo "!!! pip groups that failed:"
    printf '   %s\n' "${FAILED[@]}"
fi
echo "=== done ==="
