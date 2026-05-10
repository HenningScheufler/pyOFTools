"""
Hello pyOFTools — your first post-processor
===========================================

The shortest path from an OpenFOAM case to a CSV row: declare a
``PostProcessorBase``, decorate one function with ``@Table``, and invoke the
returned runner against a mesh. This is the exact shape a real in-situ
post-processor has — the only thing the live solver adds is calling
``runner.execute()`` and ``runner.write()`` on its own schedule.

We'll compute the mean of ``alpha.water`` on the ``cube`` baseline case.
"""

# %%
# Clone the baseline case to tmp
# ------------------------------
# Sphinx-gallery runs each script with ``cwd`` set to the script's own
# folder. We find ``tests/integration/cube/`` relative to that and copy it
# to a temporary directory so the case stays untouched.

import shutil
import tempfile
from pathlib import Path

# Import before numpy — OpenFOAM enables SIGFPE trapping and numpy's
# denormal probe trips it on import. pyOFTools ships a monkey-patch that
# disables the trap right after OpenFOAM initialisation.
import pyOFTools.patch_pybfoam  # noqa: F401


def _repo_root() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / "pyproject.toml").exists() and (p / "src" / "pyOFTools").exists():
            return p
    raise RuntimeError("Could not locate pyOFTools repo root")


BASELINE = _repo_root() / "tests" / "integration" / "cube"
CASE = Path(tempfile.mkdtemp(prefix="pyoftools_hello_")) / "cube"
shutil.copytree(BASELINE, CASE)
print(f"working case: {CASE}")

# %%
# Open the case
# -------------
# ``Time`` is the OpenFOAM clock; ``fvMesh`` loads the finite-volume mesh
# for the current time directory. We ``chdir`` into the case so OpenFOAM's
# dictionary parser resolves ``system/`` and ``constant/`` correctly.

from pybFoam import Time, fvMesh, volScalarField

# ``Time(rootPath, caseName)`` takes the case path explicitly, so we don't
# have to chdir — important under sphinx-gallery, which doesn't preserve
# cwd between cells in every context.
time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)

# ``field(mesh, "alpha.water")`` below reads from the object registry;
# read the field in first so it's there.
volScalarField.read_field(mesh, "alpha.water")

# %%
# Declare the post-processor
# --------------------------
# ``@postProcess.Table("mean_alpha.csv")`` registers a function that returns
# a ``WorkFlow``. The framework calls it each write step, appends a CSV
# row, and handles file lifecycle.

from pyOFTools.aggregators import Mean
from pyOFTools.builders import field
from pyOFTools.postprocessor import PostProcessorBase

# ``base_path`` is concatenated with ``filename`` without a separator, so
# include the trailing slash. Use an absolute path so the CSV lands inside
# the tmp case no matter what the cwd is.
postProcess = PostProcessorBase(base_path=str(CASE) + "/postProcessing/")


@postProcess.Table("mean_alpha.csv")
def mean_alpha(m):
    return field(m, "alpha.water") | Mean()


# %%
# Run it standalone
# -----------------
# In production, OpenFOAM's function-object machinery drives ``execute``
# and ``write``. For the tutorial we drive them by hand so the script runs
# without a live solver.

runner = postProcess(mesh)
runner.execute()
runner.write()
runner.end()

# %%
# Inspect the output
# ------------------
# The CSV is a single row per write call — ``time`` plus the aggregated
# value. More write calls would produce more rows.

csv_path = CASE / "postProcessing" / "mean_alpha.csv"
print(csv_path.read_text())

# %%
# What next
# ---------
#
# - :doc:`example_02_spatial_selection` — restrict the computation to a
#   sub-region with ``Box`` / ``Sphere``.
# - :doc:`example_03_binning` — turn the field into a spatial profile.
# - :doc:`/how-to/configure_controlDict` — wire this pattern into a live
#   solver via ``system/controlDict``.
