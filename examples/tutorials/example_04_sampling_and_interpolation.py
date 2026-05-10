"""
Sampling and interpolation — plane and line probes
==================================================

Many analyses don't want every cell — they want the field *on a surface* or
*along a line*. pyOFTools handles the OpenFOAM-side sampling through two
builders:

- ``plane(mesh, point, normal) | sample(mesh, field) | ...`` — cutting
  plane with an interpolated field.
- ``line(mesh, name, start, end, n_points, field)`` — uniform set with an
  interpolated field.

Both produce pipeline-ready datasets (``SurfaceDataSet`` and
``PointDataSet`` respectively — see :doc:`/explanation/datastructures`), so
the same ``Mean`` / ``Sum`` / ``VolIntegrate`` nodes you already know apply.
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
CASE = Path(tempfile.mkdtemp(prefix="pyoftools_sampling_")) / "cube"
shutil.copytree(BASELINE, CASE)

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
p_field = volScalarField.read_field(mesh, "p")

# %%
# Sample on a cutting plane
# -------------------------
# ``plane()`` returns a ``WorkFlow`` carrying only the geometry (no field
# yet). Pipe into ``sample(mesh, name)`` to interpolate a volume field onto
# the plane, then into a reducer.

from pyOFTools.aggregators import Mean, Sum
from pyOFTools.builders import area, plane, sample

mean_p_on_plane = (
    plane(mesh, point=(0.0, 0.0, 0.0), normal=(0, 0, 1))
    | sample(mesh, "p")
    | Mean()
).compute()
print(f"mean p on z=0.5 plane = {mean_p_on_plane.values[0].value:.6g}")

# ``area()`` ignores the sampled field and writes face-area magnitudes
# instead. Pipe into ``Sum`` for the total surface area.
plane_area = (
    plane(mesh, point=(0.0, 0.0, 0.0), normal=(0, 0, 1)) | area() | Sum()
).compute()
print(f"plane area            = {plane_area.values[0].value:.6g}")

# %%
# Sample on a uniform line
# ------------------------
# ``create_uniform_set(mesh, name, start, end, n_points, field)`` builds
# the point set and interpolates the given field onto it. It returns a
# ``PointDataSet`` directly (no ``WorkFlow`` wrapper), which is convenient
# when you just want the values out.
#
# The ``line()`` builder in :mod:`pyOFTools.builders` is a thin wrapper
# that also re-reads the field from disk. We already have ``p_field``
# loaded, so we call ``create_uniform_set`` directly.

from pyOFTools.sets import create_uniform_set

line_dataset = create_uniform_set(
    mesh,
    name="centreline_z",
    start=(0.0, 0.0, -0.24),
    end=(0.0, 0.0, 0.24),
    n_points=50,
    field=p_field,
)

import numpy as np

positions = np.asarray(line_dataset.geometry.positions)
distances = np.asarray(line_dataset.geometry.distance)
p_values = np.asarray(line_dataset.field)
print(f"sampled {len(p_values)} points along the z-axis")

# %%
# Plot the line profile
# ---------------------
# The gallery captures this figure and inlines it in the rendered doc.

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(distances, p_values, marker="o", markersize=3)
ax.set_xlabel("distance along line [m]")
ax.set_ylabel("p [Pa]")
ax.set_title("Pressure along a vertical line through the cube centre")
fig.tight_layout()
plt.show()

# %%
# Takeaways
# ---------
#
# - ``plane`` / ``iso_surface`` give you a ``SurfaceDataSet``; pipe into
#   ``sample(...)`` to populate the field, then into any reducer.
# - ``line`` gives you a ``PointDataSet`` with the field already on it;
#   pipe directly into a reducer or read the raw arrays.
# - Both dataset types accept the same ``Box`` / ``Sphere`` selectors and
#   ``Directional`` binner from the earlier tutorials.
#
# The how-to pages under :doc:`/auto_how_to/index` work through specific
# sampling tasks — single iso-surface area, patch flux, residual
# extraction — as independent recipes.
