"""
Spatial selection — Box, Sphere, and boolean composition
========================================================

``Box`` and ``Sphere`` are filter nodes: they take a dataset and write a
boolean ``mask`` on it, so downstream aggregators only see the elements you
selected. They compose with ``&`` (AND), ``|`` (OR), and ``~`` (NOT), which
lets you build region expressions without writing any mask logic yourself.

We'll integrate ``alpha.water`` over the whole cube, then over an off-centre
sphere, and confirm the sphere result is a strict subset.
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
CASE = Path(tempfile.mkdtemp(prefix="pyoftools_selection_")) / "cube"
shutil.copytree(BASELINE, CASE)

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
volScalarField.read_field(mesh, "alpha.water")

# %%
# Baseline: integrate over the whole domain
# -----------------------------------------
# No selector, just ``field | VolIntegrate``. This is our reference value.

from pyOFTools.aggregators import VolIntegrate
from pyOFTools.builders import field

total = (field(mesh, "alpha.water") | VolIntegrate()).compute()
total_value = total.values[0].value
print(f"whole-domain volume integral of alpha.water = {total_value:.6g}")

# The cube's initial ``alpha.water`` is uniform 0, so every integral below
# will also be 0. That's fine — the point of this tutorial is the *shape*
# of the API, not the numerical answer. A real case would have non-uniform
# initial conditions.

# %%
# Restrict to a sphere
# --------------------
# ``Sphere`` writes a mask; the downstream ``VolIntegrate`` honours it and
# sums only cell centres inside the sphere, weighted by cell volume.

from pyOFTools.spatial_selectors import Sphere

# The cube spans (-0.25, -0.25, -0.25) to (0.25, 0.25, 0.25). A sphere at
# the origin with radius 0.15 sits fully inside.
sphere_wf = (
    field(mesh, "alpha.water")
    | Sphere(center=(0.0, 0.0, 0.0), radius=0.15)
    | VolIntegrate()
)
sphere_value = sphere_wf.compute().values[0].value
print(f"sphere-only integral                         = {sphere_value:.6g}")
if total_value:
    print(f"fraction inside sphere                       = {sphere_value / total_value:.3f}")

# %%
# Compose: Box AND NOT Sphere
# ---------------------------
# Boolean composition makes complex regions declarative. Here: "inside this
# box **but not** inside the sphere". Under the hood, this builds a
# ``BinarySpatialSelector(op='and', left=Box, right=NotSpatialSelector(Sphere))``
# which evaluates both masks and combines them.

from pyOFTools.spatial_selectors import Box

region = Box(min=(-0.25, -0.25, -0.25), max=(0.25, 0.25, 0.25)) & ~Sphere(
    center=(0.0, 0.0, 0.0), radius=0.15
)

shell_wf = field(mesh, "alpha.water") | region | VolIntegrate()
shell_value = shell_wf.compute().values[0].value
print(f"box-minus-sphere integral                    = {shell_value:.6g}")

# Sanity check: the three values should sum consistently (both zero on
# this case, but on a non-uniform field the two partitions add up to the
# whole).
print(
    f"sphere + (box \\ sphere) = {sphere_value + shell_value:.6g} "
    f"(expected ≈ {total_value:.6g})"
)

# %%
# Why this is useful
# ------------------
# The same selector works on any dataset with a geometry that exposes
# ``positions`` — volume fields, sampled surfaces, line probes — because
# ``Box`` and ``Sphere`` only read ``positions`` and write ``mask``. That
# is the payoff of keeping geometry behind a Protocol
# (see :doc:`/explanation/datastructures`).
#
# Next: :doc:`example_03_binning` — instead of a single masked integral,
# produce one value per spatial bin.
