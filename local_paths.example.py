"""
Cluster-specific paths. COPY THIS FILE to local_paths.py and fill it in.

local_paths.py is gitignored on purpose: it points at the raw CALM data on the
CBU imaging space, which is neither public nor redistributable. Keeping it out
of the repository means the code can be shared without advertising where the
data lives or whose directories it sits in.

    cp local_paths.example.py local_paths.py
    # then edit local_paths.py
"""

# The qsiprep .mat holding the CALM connectomes (MATLAB v7.3 / HDF5).
SOURCE_MAT = "/path/to/calm_qsiprep_v7_3.mat"

# The CALM 800 behavioural datasheet (.csv).
DATASHEET = "/path/to/calm_800_datasheet.csv"
