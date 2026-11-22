"""
Extract solver residuals to a CSV
=================================

``residuals(mesh)`` returns a workflow seeded with an ``AggregatedDataSet``
that contains one row per ``(field, solver, metric, iteration)`` tuple. This
is what you pipe into ``@postProcess.Table("residuals.csv")`` to log solver
performance without running ``simpleFoam`` with ``solverPerformance``
enabled separately.

Residuals are populated by the running solver — a freshly loaded mesh has
an empty ``solverPerformanceDict``, so this how-to demonstrates the API
shape. Run it after a few solver steps for non-empty output.
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
# Build and inspect the residual workflow
# ---------------------------------------

from pyOFTools.builders import residuals

wf = residuals(mesh)
dataset = wf.compute()

print(f"residuals returned {len(dataset.values)} rows")
if dataset.values:
    print("headers:", dataset.headers)
    for row in dataset.grouped_values[:5]:
        print("  ", row)
else:
    print("(empty — solverPerformanceDict has not been populated by a solver run)")

# %%
# In-situ usage
# -------------
# In practice, this is what the decorator looks like:
#
# .. code-block:: python
#
#    from pyOFTools.postprocessor import PostProcessorBase
#    from pyOFTools.builders import residuals
#
#    postProcess = PostProcessorBase()
#
#    @postProcess.Table("residuals.csv")
#    def solver_residuals(mesh):
#        return residuals(mesh)
#
# The CSV gets one row per field per inner iteration per write step — long
# format, trivial to pivot with pandas.
