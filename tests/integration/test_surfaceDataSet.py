"""Tests for SurfaceDataSet functionality using sampledSurface geometries."""

import os

import pytest
from pybFoam import (
    Time,
    Word,
    fvMesh,
    scalarField,
)
from pybFoam.sampling import (
    SampledCuttingPlaneConfig,
    sampledSurface,
)

from pyOFTools.aggregators import Sum
from pyOFTools.datasets import SurfaceDataSet
from pyOFTools.geometry import SampledSurfaceAdapter
from pyOFTools.workflow import WorkFlow


@pytest.fixture(scope="function")
def change_to_cube_dir(request):
    """Change to test directory for OpenFOAM case access."""

    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


def create_time_mesh():
    """Create OpenFOAM mesh from test case.

    Returns:
        Tuple of (Time, fvMesh) for the test case
    """
    time = Time(".", ".")
    mesh = fvMesh(time)
    return time, mesh


def test_create_simple_scalar_surface_dataset(change_to_cube_dir):
    """Test creation of SurfaceDataSet with scalar field."""
    time, mesh = create_time_mesh()

    # Create a cutting plane surface using correct configuration
    plane_config = SampledCuttingPlaneConfig(point=[0.0, 0.0, 0.0], normal=[0.0, 0.0, 1.0])
    plane_dict = plane_config.to_foam_dict()

    # Create the sampledSurface
    plane_surface = sampledSurface.New(Word("testCuttingPlane"), mesh, plane_dict)

    assert plane_surface is not None
    assert plane_surface.name() == "testCuttingPlane"

    # Update the surface
    assert plane_surface.update()

    # Get surface geometry
    points = plane_surface.points()  # vertices of the surface
    magSf = plane_surface.magSf()  # face areas

    assert len(points) > 0
    assert len(magSf) > 0
    # Note: points are vertices, magSf are faces - they don't have to match
    assert len(magSf) > 0

    # Create adapter for the surface
    adapter = SampledSurfaceAdapter(plane_surface)

    # Create a dummy scalar field for the surface (one value per face)
    field = scalarField([1.0] * len(magSf))

    # Create SurfaceDataSet
    surface_dataset = SurfaceDataSet(name="test_scalar_surface", field=field, geometry=adapter)

    surface_dataset

    assert surface_dataset is not None
    assert surface_dataset.name == "test_scalar_surface"
    assert surface_dataset.field == field
    assert surface_dataset.geometry is not None


def test_create_simple_scalar_surface_dataset_workflow(change_to_cube_dir):
    """Test creation of SurfaceDataSet with scalar field."""
    time, mesh = create_time_mesh()

    # Create a cutting plane surface using correct configuration
    plane_config = SampledCuttingPlaneConfig(point=[0.0, 0.0, 0.0], normal=[0.0, 0.0, 1.0])
    plane_dict = plane_config.to_foam_dict()

    # Create the sampledSurface
    plane_surface = sampledSurface.New(Word("testCuttingPlane"), mesh, plane_dict)
    plane_surface.update()
    field = scalarField(plane_surface.magSf())

    # Create SurfaceDataSet
    surface_dataset = SurfaceDataSet(
        name="test_scalar_surface", field=field, geometry=SampledSurfaceAdapter(plane_surface)
    )

    w = WorkFlow(initial_dataset=surface_dataset).then(Sum())

    result = w.compute()
    assert result.values[0].value == pytest.approx(0.25)
