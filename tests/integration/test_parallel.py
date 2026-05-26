"""
Parallel integration tests for pyOFTools.

These tests are marked with @pytest.mark.parallel and must be run under MPI:
    mpirun -np 2 uv run pytest -m parallel
"""

import os
from collections.abc import Iterator

import numpy as np
import pytest
from pybFoam import Time, fvMesh, volScalarField

from pyOFTools import examples_root
from pyOFTools.aggregators import Max, Mean, Min, Sum, VolIntegrate
from pyOFTools.builders import field


@pytest.fixture
def time_mesh(request: pytest.FixtureRequest) -> Iterator[tuple[Time, fvMesh]]:
    """Change to cube dir and create mesh — each MPI rank reads its processorN/."""
    os.chdir(str(examples_root() / "cube"))
    time = Time(".", ".")
    mesh = fvMesh(time)
    yield time, mesh
    os.chdir(request.config.invocation_params.dir)


@pytest.mark.parallel
def test_vol_integrate_parallel(time_mesh: tuple[Time, fvMesh]) -> None:
    """Test VolIntegrate produces correct result across MPI ranks."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")
    workflow = field(mesh, "p") | VolIntegrate()
    result = workflow.compute()

    assert result is not None
    assert len(result.values) > 0
    val = float(result.values[0].value)
    assert np.isfinite(val)


@pytest.mark.parallel
def test_sum_parallel(time_mesh: tuple[Time, fvMesh]) -> None:
    """Test Sum aggregation across MPI ranks."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")
    workflow = field(mesh, "p") | Sum()
    result = workflow.compute()

    assert result is not None
    assert len(result.values) > 0
    val = float(result.values[0].value)
    assert np.isfinite(val)


@pytest.mark.parallel
def test_mean_parallel(time_mesh: tuple[Time, fvMesh]) -> None:
    """Test Mean aggregation across MPI ranks."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")
    workflow = field(mesh, "p") | Mean()
    result = workflow.compute()

    assert result is not None
    assert len(result.values) > 0
    val = float(result.values[0].value)
    assert np.isfinite(val)


@pytest.mark.parallel
def test_min_max_parallel(time_mesh: tuple[Time, fvMesh]) -> None:
    """Test Min and Max aggregation across MPI ranks."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")

    min_result = (field(mesh, "p") | Min()).compute()
    max_result = (field(mesh, "p") | Max()).compute()

    min_val = float(min_result.values[0].value)
    max_val = float(max_result.values[0].value)

    assert np.isfinite(min_val)
    assert np.isfinite(max_val)
    assert min_val <= max_val
