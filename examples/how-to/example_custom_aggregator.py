"""
Write a custom aggregator node
==============================

Aggregators are the "reduce to a number" step of a pipeline. The built-in
ones (``Sum``, ``Mean``, ``Min``, ``Max``, ``VolIntegrate``, ``SurfIntegrate``)
cover most cases, but sometimes you need a specific reduction. Here we
build a ``Variance`` node from scratch, verify it matches a numpy
reference, and slot it into the pipeline.

Details on the node contract live in :doc:`/explanation/custom_nodes` —
this page is the practical walk-through.
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

from pybFoam import Time, fvMesh, volScalarField

time = Time(str(CASE.parent), CASE.name)
mesh = fvMesh(time)
volScalarField.read_field(mesh, "alpha.water")

# %%
# Define ``Variance``
# -------------------
# Subclass ``BaseModel``, declare a unique ``type`` literal, implement
# ``compute(dataset) -> AggregatedDataSet``, register with ``@Node.register()``.

from typing import Literal, Optional

import numpy as np
from pydantic import BaseModel

from pyOFTools.datasets import AggregatedData, AggregatedDataSet, DataSets
from pyOFTools.node import Node


@Node.register()
class Variance(BaseModel):
    """Sample variance of the field. Ignores mask/groups for brevity —
    production nodes should honour both."""

    type: Literal["variance"] = "variance"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        values = np.asarray(dataset.field)
        var = float(np.var(values, ddof=0))
        return AggregatedDataSet(
            name=self.name or f"{dataset.name}_variance",
            values=[AggregatedData(value=var)],
        )


# %%
# Use it in a pipe
# ----------------
# Once registered, ``Variance`` behaves exactly like a built-in node. The
# ``|`` operator, ``WorkFlow.then``, and Pydantic validation all work
# unchanged.

from pyOFTools.builders import field

result = (field(mesh, "alpha.water") | Variance()).compute()
variance_from_node = result.values[0].value
print(f"Var(alpha.water) via node = {variance_from_node:.6g}")

# %%
# Verify against numpy
# --------------------
# Sanity-check by reading the same field raw and computing the variance in
# numpy directly. They should match to floating-point precision.

alpha = volScalarField.from_registry(mesh, "alpha.water")
raw_values = np.asarray(alpha["internalField"])
variance_from_numpy = float(np.var(raw_values, ddof=0))
print(f"Var(alpha.water) via numpy = {variance_from_numpy:.6g}")
assert np.isclose(variance_from_node, variance_from_numpy), "node and numpy disagree"

# %%
# Production-grade version
# ------------------------
# The node above is intentionally minimal. Two things a real node should
# handle:
#
# 1. **Mask and groups** — filter by ``dataset.mask`` and reduce per
#    ``dataset.groups`` id. The ``pyOFTools.aggregation`` module has
#    MPI-aware helpers (``aggregation.mean``, ``aggregation.sum``) that do
#    this for you; see the ``StdDev`` example in
#    :doc:`/explanation/custom_nodes`.
# 2. **Parallel correctness** — the node above computes a local variance
#    per rank. For a global variance, compute E[x], E[x^2] with the
#    MPI-aware helpers and combine.
