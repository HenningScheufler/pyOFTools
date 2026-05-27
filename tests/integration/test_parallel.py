"""
Parallel integration tests for pyOFTools.

These tests are marked with @pytest.mark.parallel and must be run under MPI:
    mpirun -np 2 uv run pytest -m parallel
"""

import os
import subprocess
from collections.abc import Iterator

import numpy as np
import pytest
from pybFoam import Time, argList, fvMesh, volScalarField

from pyOFTools import examples_root
from pyOFTools.aggregators import Max, Mean, Min, Sum, VolIntegrate
from pyOFTools.builders import field


@pytest.fixture(scope="session")
def time_mesh(request: pytest.FixtureRequest) -> Iterator[tuple[Time, fvMesh]]:
    """Session-scoped mesh that each MPI rank reads from its own ``processorN/``.

    Only the master rank runs ``./AllrunParallel`` (blockMesh + decomposePar).
    Workers don't need to wait on a sentinel: ``argList(-parallel)`` calls
    ``MPI_Init``, a collective barrier, and the master only reaches it *after*
    decomposing — so workers block there until the mesh exists. Building ``Time``
    from that ``argList`` initialises OpenFOAM's MPI Pstream, so aggregations
    reduce across ranks. Session-scoped because MPI initialises once per process.
    """
    case_dir = str(examples_root() / "cube")
    rank = int(os.environ.get("OMPI_COMM_WORLD_RANK", "0"))

    if rank == 0:
        subprocess.run(["./AllrunParallel"], cwd=case_dir, check=True)

    os.chdir(case_dir)
    args = argList(["pyOFTools", "-parallel"])
    runtime = Time(args)
    mesh = fvMesh(runtime)
    volScalarField.read_field(mesh, "p")  # register once; tests use from_registry

    yield runtime, mesh

    os.chdir(request.config.invocation_params.dir)
    if rank == 0:
        subprocess.run(["./Allclean"], cwd=case_dir, check=False)


@pytest.mark.parallel
def test_vol_integrate_parallel(time_mesh: tuple[Time, fvMesh]) -> None:
    """Test VolIntegrate produces correct result across MPI ranks."""
    _, mesh = time_mesh

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

    min_result = (field(mesh, "p") | Min()).compute()
    max_result = (field(mesh, "p") | Max()).compute()

    min_val = float(min_result.values[0].value)
    max_val = float(max_result.values[0].value)

    assert np.isfinite(min_val)
    assert np.isfinite(max_val)
    assert min_val <= max_val
