"""
Run live with the solver, then plot
===================================

So far we drove ``execute`` / ``write`` by hand to keep tutorials self-contained.
The whole point of pyOFTools, though, is that the running solver calls them
for you. This tutorial closes the loop:

1. write a ``postProcess.py`` to the cloned case that combines the monitors
   from tutorials 02-04,
2. truncate the case's ``endTime`` so the run completes in seconds,
3. run ``compressibleInterFoam`` — OpenFOAM picks up the
   ``pyPostProcessing`` function object from ``system/controlDict`` and calls
   the registered ``@Table`` outputs on every step,
4. load the resulting CSVs with pandas and plot the time-series.

The wiring in ``system/controlDict`` is already there in the ``damBreak``
case — see :doc:`example_02_first_postprocessor` for the snippet.
"""

# %%
# Clone the case
# --------------

import pyOFTools.patch_pybfoam  # noqa: F401

import os
import subprocess

import numpy as np  # noqa: F401  — imported early to dodge SIGFPE

from pyOFTools import clone_example

CASE = clone_example("damBreak")
print(f"working case: {CASE}")

# %%
# The post-processor file
# -----------------------
# OpenFOAM's ``pyPostProcessing`` function object imports ``postProcess.py``
# from the case directory and instantiates the ``postProcess`` class with the
# mesh, then calls ``execute`` / ``write`` / ``end`` on it. The damBreak case
# already ships such a file, and ``clone_example`` brought it across with the
# rest of the case:
#
# .. literalinclude:: ../../examples/damBreak/postProcess.py
#    :language: python
#    :caption: examples/damBreak/postProcess.py
#
# Four ``@Table`` outputs — water volume, interface area, mass profile along
# x, mean pressure on a horizontal mid-plane — combine the patterns from
# tutorials 02-04 into the single class the live solver will call.

# %%
# Trim ``endTime`` for the tutorial
# ---------------------------------
# The shipped ``controlDict`` runs to ``t = 2.0`` — fine for a real study,
# too slow for a doc build. ``dictionary.read`` parses it, ``cd.set`` patches
# the entry, ``cd.write`` puts it back as a valid OpenFOAM dictionary
# (preserving format, comments, and adjacent entries).

from pybFoam import dictionary

control_dict_path = CASE / "system" / "controlDict"
cd = dictionary.read(str(control_dict_path))
cd.set("endTime", 0.05)
cd.write(str(control_dict_path))

# %%
# Mesh, set fields, run the solver
# --------------------------------
# Same sequence ``./Allrun`` would do. The mesh is built in-process with
# ``generate_blockmesh``; setFields and the solver run as subprocesses
# (the solver is a C++ binary, so no in-process equivalent).

from pybFoam import Time, argList, dictionary
from pybFoam.meshing import generate_blockmesh

env = {**os.environ}


def run(cmd):
    res = subprocess.run(cmd, cwd=CASE, env=env, capture_output=True, text=True, check=True)
    # OpenFOAM is chatty — show the tail so the gallery output stays useful.
    tail = "\n".join(res.stdout.splitlines()[-5:])
    print(f"$ {' '.join(cmd)}\n{tail}\n")


time = Time(argList([str(CASE), "-case", str(CASE)]))
generate_blockmesh(time, dictionary.read(str(CASE / "system" / "blockMeshDict")))
run(["pyoftools", "setFields", "system/setFields.py"])
run(["compressibleInterFoam"])

# %%
# Load the CSVs
# -------------
# Each ``@Table`` produced one CSV under ``postProcessing/``. They have a
# ``time`` column plus the named value column (and ``group`` for binned
# outputs).

import pandas as pd

vol = pd.read_csv(CASE / "postProcessing" / "water_volume.csv")
area_df = pd.read_csv(CASE / "postProcessing" / "interface_area.csv")
mass = pd.read_csv(CASE / "postProcessing" / "mass_profile_x.csv")
plane_p = pd.read_csv(CASE / "postProcessing" / "mean_p_midplane.csv")

print(vol.head())
print(mass.head())

# %%
# Plot the monitors
# -----------------
# Four panels: water volume (should be conserved-ish), interface area (grows
# as the wave breaks up), per-bin mass along x (the wave front advances),
# and mean pressure on the mid-plane.

import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))

axes[0, 0].plot(vol["time"], vol["water_volume"], marker="o", markersize=3)
axes[0, 0].set(xlabel="time [s]", ylabel="water volume [m³]", title="Total water volume")

axes[0, 1].plot(area_df["time"], area_df["interface_area"], marker="o", markersize=3)
axes[0, 1].set(xlabel="time [s]", ylabel="interface area [m²]", title="α = 0.5 interface area")

# Long-format: one row per (time, bin). Pivot so each bin is its own line.
mass_wide = mass.pivot(index="time", columns="group", values="mass")
mass_wide.plot(ax=axes[1, 0], marker="o", markersize=3)
axes[1, 0].set(xlabel="time [s]", ylabel="mass per bin [kg]", title="Mass along x (per bin)")
axes[1, 0].legend(title="bin", fontsize=8)

axes[1, 1].plot(plane_p["time"], plane_p["mean_p_midplane"], marker="o", markersize=3)
axes[1, 1].set(xlabel="time [s]", ylabel="mean p [Pa]", title="Mean p on y = 0.146 m plane")

fig.tight_layout()
plt.show()

# %%
# Visualise the interface at the final time
# -----------------------------------------
# The CSVs only carry scalars; for the geometry of what just happened, drop
# back to pyvista. We pick the α = 0.5 iso-surface — the gas–liquid
# interface — at the end of the run and colour it by pressure.

import pyvista as pv

from pybFoam import pyvista_read

reader = pyvista_read(CASE)
reader.set_active_time_value(reader.time_values[-1])
internal = reader.read()["internalMesh"]
interface = internal.contour(isosurfaces=[0.5], scalars="alpha.water")

plotter = pv.Plotter(window_size=(640, 400), off_screen=True)
plotter.add_mesh(internal.outline(), color="gray")
plotter.add_mesh(
    interface,
    scalars="p",
    cmap="coolwarm",
    scalar_bar_args={"title": "p [Pa]"},
)
plotter.view_isometric()
plotter.show()

# %%
# Where to go next
# ----------------
#
# - :doc:`/auto_how_to/index` — point-in-time recipes for specific tasks
#   (iso-surface area, residual extraction, custom aggregator).
# - :doc:`/how-to/configure_controlDict` — full ``pyPostProcessing``
#   reference including ``writeControl`` variants and HDF5 output.
# - :doc:`/explanation/datastructures` — what's actually flowing through the
#   pipeline (geometry, mask, groups, field) and how custom nodes fit in.
