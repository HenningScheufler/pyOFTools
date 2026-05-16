"""
Sample a field along a line
===========================

``line(mesh, name, start, end, n_points, field_name)`` builds a
``PointDataSet`` with the requested field already interpolated onto evenly
spaced points between ``start`` and ``end``. This is the pyOFTools-side
equivalent of OpenFOAM's ``uniform`` set in ``system/sampleDict``.
"""

# %%
# Open the case
# -------------

import os
import subprocess

import pyOFTools.patch_pybfoam  # noqa: F401
from pyOFTools import clone_example

CASE = clone_example("damBreak")
subprocess.run(
    ["./Allrun"], cwd=CASE, check=True,
    env={**os.environ}, capture_output=True, text=True,
)

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
p_field = volScalarField.read_field(mesh, "p")

# %%
# Build the line
# --------------
# A vertical probe through the middle of the water column.
# ``create_uniform_set`` takes the field object directly (``p_field``),
# which avoids re-reading it — the ``line()`` builder in
# :mod:`pyOFTools.builders` would do a second ``read_field`` and
# double-register the field in OpenFOAM.

from pyOFTools.sets import create_uniform_set

dataset = create_uniform_set(
    mesh,
    name="vertical_p",
    start=(0.146, 0.0, 0.0073),
    end=(0.146, 0.584, 0.0073),
    n_points=100,
    field=p_field,
)

# %%
# Plot it
# -------

import matplotlib.pyplot as plt
import numpy as np

distance = np.asarray(dataset.geometry.distance)
pressure = np.asarray(dataset.field)

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(distance, pressure)
ax.set_xlabel("distance along line [m]")
ax.set_ylabel("p [Pa]")
ax.set_title("Pressure along a vertical line (damBreak, t=0)")
fig.tight_layout()
plt.show()

# %%
# Aggregate instead of plot
# -------------------------
# The same ``PointDataSet`` flows into any reducer node. ``Mean`` gives the
# arithmetic mean over the sampled points (not a length-weighted mean — use
# a ``Sum`` with a manual scaling factor for that).

from pyOFTools.aggregators import Max, Mean
from pyOFTools.workflow import WorkFlow

mean_p = (WorkFlow(initial_dataset=dataset) | Mean()).compute()
max_p = (WorkFlow(initial_dataset=dataset) | Max()).compute()
print(f"mean p along line = {mean_p.values[0].value:.4g} Pa")
print(f"max  p along line = {max_p.values[0].value:.4g} Pa")
