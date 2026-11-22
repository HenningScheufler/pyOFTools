"""
Compute a surface integral over a patch
=======================================

``SurfIntegrate`` weights by face-area magnitude instead of cell volume. On
a boundary patch, that gives you per-patch totals (mass flux, force,
heat flux) as long as the per-face quantity you hand it is the right
integrand.

Here we compute the area of the ``lowerWall`` patch on the damBreak case by
feeding ``area()`` into ``Sum`` — same idea, simpler integrand.
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
    ["./Allrun"],
    cwd=CASE,
    check=True,
    env={**os.environ},
    capture_output=True,
    text=True,
)

from pybFoam import Time, fvMesh

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)

# %%
# Patch area via ``create_patch_surface`` + ``area`` + ``Sum``
# ------------------------------------------------------------
# ``create_patch_surface`` returns a sampledSurface spanning the given
# patches. Wrap it in a ``SurfaceDataSet`` yourself (there's no builder for
# this yet), then ``area()`` writes face-area magnitudes onto the dataset
# and ``Sum`` reduces them.

from pyOFTools.aggregators import Sum
from pyOFTools.builders import area
from pyOFTools.datasets import SurfaceDataSet
from pyOFTools.geometry import SampledSurfaceAdapter
from pyOFTools.surfaces import create_patch_surface
from pyOFTools.workflow import WorkFlow

patch_surface = create_patch_surface(mesh, name="lower", patches=["lowerWall"])
patch_ds = SurfaceDataSet(
    name="lowerWall",
    geometry=SampledSurfaceAdapter(patch_surface),
)

patch_area = (WorkFlow(initial_dataset=patch_ds) | area() | Sum()).compute()
print(f"lowerWall patch area = {patch_area.values[0].value:.6g} m^2")

# %%
# Surface-weighted integral of a sampled field
# --------------------------------------------
# To compute a flux-like quantity, interpolate a volume field onto the
# patch, then use ``SurfIntegrate`` (same as ``sample | Sum`` but weighted
# by face area):
#
# .. code-block:: python
#
#    from pyOFTools.aggregators import SurfIntegrate
#    from pyOFTools.builders import sample
#
#    flux = (
#        WorkFlow(initial_dataset=patch_ds)
#        | sample(mesh, "p")
#        | SurfIntegrate()
#    ).compute()
#
# The surface variant is in :doc:`example_sample_plane` where we also
# visualise the sampled field.
