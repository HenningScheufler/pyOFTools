"""
Measure the interface area of a VOF free surface
================================================

In a volume-of-fluid simulation, the ``alpha.water = 0.5`` iso-surface is a
good proxy for the liquid–gas interface. Its area is a useful diagnostic:
it grows during breakup, collapses on coalescence. pyOFTools' ``iso_surface``
builder + ``Sum`` gives you the number in one line.
"""

# %%
# Open the case
# -------------

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pyOFTools.patch_pybfoam  # noqa: F401


def _repo_root() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "pyproject.toml").exists() and (p / "src" / "pyOFTools").exists():
            return p
    raise RuntimeError("Could not locate pyOFTools repo root")


def _prepare_dambreak(prefix: str) -> Path:
    baseline = _repo_root() / "example" / "damBreak"
    case = Path(tempfile.mkdtemp(prefix=prefix)) / "damBreak"
    shutil.copytree(baseline, case)
    subprocess.run(
        ["./Allrun"], cwd=case, check=True,
        env={**os.environ}, capture_output=True, text=True,
    )
    return case


CASE = _prepare_dambreak("pyoftools_iso_area_")

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
volScalarField.read_field(mesh, "alpha.water")

# %%
# Iso-surface area
# ----------------
# ``iso_surface`` returns a ``WorkFlow`` seeded with a ``SurfaceDataSet``
# whose field slot is *empty*. Pipe into ``area()`` to populate the field
# with face-area magnitudes, then ``Sum`` to reduce.

from pyOFTools.aggregators import Sum
from pyOFTools.builders import area, iso_surface

result = (
    iso_surface(mesh, iso_field="alpha.water", iso_value=0.5)
    | area()
    | Sum()
).compute()
interface_area = result.values[0].value
print(f"interface area at t=0: {interface_area:.6g} m^2")

# %%
# Over time, wire this into a @Table
# ----------------------------------
# In-situ, you register the computation once and the framework calls it
# each write step:
#
# .. code-block:: python
#
#    from pyOFTools.postprocessor import PostProcessorBase
#    postProcess = PostProcessorBase()
#
#    @postProcess.Table("interface_area.csv")
#    def interface_area(mesh):
#        return iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()
#
# See :doc:`/how-to/configure_controlDict` for the ``system/controlDict``
# wiring.
