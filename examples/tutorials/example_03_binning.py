"""
Binning — turn a field into a spatial profile
=============================================

``Directional`` is a binner: it partitions a dataset's elements into groups
by their projection onto a direction vector and writes the group id onto
``dataset.groups``. Downstream aggregators then emit one value per group
instead of a single scalar, giving you a 1-D profile.

We'll bin ``alpha.water`` along the x-axis on the cube case and plot the
profile with matplotlib.
"""

# %%
# Open the cube case
# ------------------

import shutil
import tempfile
from pathlib import Path

import pyOFTools.patch_pybfoam  # noqa: F401


def _repo_root() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "pyproject.toml").exists() and (p / "src" / "pyOFTools").exists():
            return p
    raise RuntimeError("Could not locate pyOFTools repo root")


BASELINE = _repo_root() / "tests" / "integration" / "cube"
CASE = Path(tempfile.mkdtemp(prefix="pyoftools_binning_")) / "cube"
shutil.copytree(BASELINE, CASE)

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
volScalarField.read_field(mesh, "alpha.water")

# %%
# Build a 10-bin x-profile
# ------------------------
# ``bins`` are the bin *edges*: N edges define N-1 bins (plus under/over
# flow). ``direction`` and ``origin`` set the axis of projection —
# ``(1, 0, 0)`` from origin ``(0, 0, 0)`` is plain x-coordinate.

import numpy as np

from pyOFTools.aggregators import VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.builders import field

edges = np.linspace(0.0, 1.0, 11).tolist()
profile_wf = (
    field(mesh, "alpha.water")
    | Directional(bins=edges, direction=(1.0, 0.0, 0.0), origin=(0.0, 0.0, 0.0))
    | VolIntegrate()
)
profile = profile_wf.compute()

# ``AggregatedDataSet.grouped_values`` gives CSV-ready rows: ``[value,
# group_id]``. ``np.digitize`` assigns 0 for below-first-edge, N for
# above-last-edge; here we just ignore those two and keep the interior
# bins.
rows = np.asarray(profile.grouped_values)
values = rows[:, 0]
group_ids = rows[:, 1].astype(int)

print(f"{len(values)} groups returned")
for g, v in zip(group_ids, values):
    print(f"  bin {g:>2}: {v:.4g}")

# %%
# Plot the profile
# ----------------
# Turn bin ids into bin centres for plotting. Sphinx-gallery captures the
# figure and inlines it in the rendered doc page.

import matplotlib.pyplot as plt

centres = 0.5 * (np.array(edges[:-1]) + np.array(edges[1:]))
# keep only interior bins (group ids 1..N-1)
mask = (group_ids >= 1) & (group_ids <= len(edges) - 1)
plot_x = centres[group_ids[mask] - 1]
plot_y = values[mask]

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.bar(plot_x, plot_y, width=(edges[1] - edges[0]) * 0.9, edgecolor="black")
ax.set_xlabel("x [m]")
ax.set_ylabel("∫ α dV per bin")
ax.set_title("alpha.water volume distribution along x")
fig.tight_layout()
plt.show()

# %%
# Where to next
# -------------
#
# - Swap ``VolIntegrate`` for ``Mean`` to get the bin-averaged value
#   instead of the bin-integrated value.
# - Stack a ``Sphere`` / ``Box`` selector *before* ``Directional`` to
#   profile only the region you care about — the mask and groups
#   compose (see :doc:`example_02_spatial_selection`).
# - :doc:`example_04_sampling_and_interpolation` — instead of binning the
#   native cells, sample the field onto a plane or a line.
