"""
Direct tests for the SampledSurfaceAdapter protocol compliance.

This test file focuses on testing the adapter's protocol implementation
and internal consistency. Surface creation and usage are tested elsewhere.
"""

import os

import pytest
from pybFoam import Time, Word, argList, createMesh, dictionary, vector
from pybFoam.sampling import sampledSurface

from pyOFTools.geometry import SampledSurfaceAdapter


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def runTime(change_test_dir):
    """Create OpenFOAM Time object."""
    args = argList(["solver"])
    return Time(args)


@pytest.fixture
def mesh(runTime):
    """Create OpenFOAM mesh."""
    return createMesh(runTime)


@pytest.fixture
def plane_surface(mesh):
    """Create a plane surface for testing."""
    surf_dict = dictionary()
    surf_dict.add("type", Word("plane"))
    surf_dict.add("point", vector(0.0, 0.0, 0.0))
    surf_dict.add("normal", vector(1.0, 0.0, 0.0))

    surface = sampledSurface.New(Word("testPlane"), mesh, surf_dict)
    surface.update()
    return surface


def test_adapter_protocol_compliance(plane_surface):
    """Test that the adapter satisfies the SurfaceMesh protocol."""
    adapter = SampledSurfaceAdapter(plane_surface)

    # Check that all required protocol methods/properties exist
    assert hasattr(adapter, "points")
    assert hasattr(adapter, "face_centers")
    assert hasattr(adapter, "face_areas")
    assert hasattr(adapter, "face_area_magnitudes")
    assert hasattr(adapter, "total_area")

    # All should be accessible and return valid data
    assert len(adapter.points) > 0
    assert len(adapter.face_centers) > 0
    assert len(adapter.face_areas) > 0
    assert len(adapter.face_area_magnitudes) > 0
    assert adapter.total_area > 0


def test_adapter_geometry_consistency(plane_surface):
    """Test that all geometric properties are internally consistent."""
    adapter = SampledSurfaceAdapter(plane_surface)

    # Number of face centers, face areas, and magnitudes should all match
    n_faces = len(adapter.face_centers)
    assert len(adapter.face_areas) == n_faces
    assert len(adapter.face_area_magnitudes) == n_faces

    # Total area should equal sum of magnitudes
    expected_total = sum(adapter.face_area_magnitudes)
    assert abs(adapter.total_area - expected_total) < 1e-10

    # All magnitudes should be positive
    assert all(m > 0 for m in adapter.face_area_magnitudes)
