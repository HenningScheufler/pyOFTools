"""
Compute a volume integral
=========================

``VolIntegrate`` is the canonical reducer for volume fields: it multiplies
by cell volume and sums. Use it whenever "how much" is the question —
total mass, total energy, integrated source term.

We compute the total water volume in the ``damBreak`` case at t=0.
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
volScalarField.read_field(mesh, "alpha.water")

# %%
# Integrate
# ---------
# ``field | VolIntegrate`` — read as "wrap the field, integrate it by
# cell volumes". The result is an ``AggregatedDataSet`` with one value.

from pyOFTools.aggregators import VolIntegrate
from pyOFTools.builders import field

result = (field(mesh, "alpha.water") | VolIntegrate()).compute()
total_water_volume = result.values[0].value
print(f"total water volume at t=0: {total_water_volume:.6g} m^3")

# %%
# Write it to a CSV
# -----------------
# For a standalone script, the raw value is usually enough. But if you are
# going to wire this into ``@postProcess.Table`` later (see
# :doc:`/how-to/configure_controlDict`), it is useful to know that the CSV
# row you get is exactly what ``AggregatedDataSet.grouped_values`` returns.

print("headers:", result.headers)
print("rows:   ", result.grouped_values)
