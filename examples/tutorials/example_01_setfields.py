"""
Set initial conditions with ``pyoftools setFields``
===================================================

Before a solver can do anything useful, the case needs initial fields. pyOFTools
ships a small CLI — ``pyoftools setFields`` — that runs a Python (or JSON) spec
to populate ``0/`` fields, using the *same* ``Box`` / ``Sphere`` / ``&`` / ``|``
/ ``~`` selectors you'll use later for post-processing. That symmetry is the
point: one geometric language for both ends of the run.

In this tutorial you'll:

- clone the ``damBreak`` baseline case,
- read its bundled ``system/setFields.py`` to see what an in-Python setFields
  script looks like,
- run it via the CLI and verify ``0/alpha.water`` is no longer uniform,
- render the resulting field with pyvista.

The next tutorial picks up from a case prepared this way and instruments the
solver run.
"""

# %%
# Imports
# -------
# ``patch_pybfoam`` disables OpenFOAM's SIGFPE trap so numpy/pyvista don't
# crash on later use. We import numpy up front, before the first OpenFOAM
# call, so its denormal-probe import never sees the trap re-enabled.

import pyOFTools.patch_pybfoam  # noqa: F401

import subprocess

import numpy as np  # noqa: F401  — imported early to dodge SIGFPE
import pyvista as pv

from pyOFTools import clone_example

# %%
# Clone the case
# --------------
# :func:`pyOFTools.clone_example` copies ``examples/damBreak`` to a tmp dir and
# restores ``0.orig/`` → ``0/``. The on-disk baseline is never touched.

CASE = clone_example("damBreak")
print(f"working case: {CASE}")

# %%
# Build the mesh
# --------------
# ``setFields`` writes into ``0/`` based on cell positions, so the mesh has to
# exist first. The ``damBreak`` case ships with ``system/blockMeshDict``;
# :func:`pybFoam.meshing.generate_blockmesh` reads it and writes the resulting
# polyMesh into ``constant/`` — same effect as running the ``blockMesh``
# binary, just in-process.

from pybFoam import Time, argList, dictionary
from pybFoam.meshing import generate_blockmesh

time = Time(argList([str(CASE), "-case", str(CASE)]))
generate_blockmesh(time, dictionary.read(str(CASE / "system" / "blockMeshDict")))

# %%
# What the setFields script looks like
# ------------------------------------
# The bundled script populates ``alpha.water`` to ``1`` inside a box (the
# initial water column) **or** inside a sphere — the very same ``Box`` /
# ``Sphere`` you'll see again in :doc:`example_03_profiles_and_selectors`. The
# script ends with ``write(alpha)`` so the modified field hits disk.
#
# .. literalinclude:: ../../examples/damBreak/system/setFields.py
#    :language: python
#    :caption: examples/damBreak/system/setFields.py

# %%
# Run the CLI
# -----------
# ``pyoftools setFields <path>`` dispatches on the file extension: ``.py`` is
# executed via :func:`runpy.run_path`, ``.json`` is loaded as a declarative
# spec (a ``system/setFields.json`` ships alongside as the no-code variant).
#
# The script uses ``argList(["."])``, so we run from inside the case.

result = subprocess.run(
    ["pyoftools", "setFields", "system/setFields.py"],
    cwd=CASE,
    check=True,
    capture_output=True,
    text=True,
)
print(result.stdout)

# %%
# Verify the result (numerically)
# -------------------------------
# Build the fvMesh on top of the runtime we already have and read the field
# back from disk. Before setFields, ``alpha.water`` was uniform 0; afterwards
# a fraction of the cells should read 1.

from pybFoam import fvMesh, volScalarField

mesh = fvMesh(time)
alpha = volScalarField.read_field(mesh, "alpha.water")

values = np.asarray(alpha["internalField"])
filled = int((values > 0.5).sum())
print(f"total cells     = {values.size}")
print(f"cells with α=1  = {filled} ({100 * filled / values.size:.1f}%)")
print(f"min / max α     = {values.min():.3f} / {values.max():.3f}")

# %%
# Verify the result (visually)
# ----------------------------
# :func:`pybFoam.pyvista_read` wraps pyvista's ``POpenFOAMReader``, so we can
# open the case directly. Slicing at the depth midplane (``z = 0.0075``) gives
# a 2-D view; colouring by ``alpha.water`` shows the rectangular water column
# plus the spherical inclusion the script added at the origin.

from pybFoam import pyvista_read

reader = pyvista_read(CASE, time=0.0)
internal = reader.read()["internalMesh"]
slice_mid = internal.slice(normal="z", origin=(0.292, 0.292, 0.0075))

plotter = pv.Plotter(window_size=(640, 360), off_screen=True)
plotter.add_mesh(
    slice_mid,
    scalars="alpha.water",
    cmap="Blues",
    clim=(0.0, 1.0),
    show_edges=False,
    scalar_bar_args={"title": "α (water)"},
)
plotter.view_xy()
plotter.show()

# %%
# JSON variant
# ------------
# For the common case of "set this field to this value in this region", the
# Python script is overkill. ``system/setFields.json`` is the declarative form:
# a list of field assignments. The CLI loads it with the same entry point.
#
# .. literalinclude:: ../../examples/damBreak/system/setFields.json
#    :language: json
#    :caption: examples/damBreak/system/setFields.json

# %%
# Next
# ----
#
# - :doc:`example_02_first_postprocessor` — instrument the run with an
#   in-situ post-processor and produce a CSV monitor.
# - :doc:`/explanation/datastructures` — the geometry/mask/groups contract
#   that lets the same selectors work on both setFields *and* the
#   post-processing pipeline.
