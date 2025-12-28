"""
Tests for the SampledSurfaceAdapter class.
"""

import pytest
from pybFoam import Time, Word, argList, createMesh, dictionary, vector
from pybFoam.sampling import sampledSurface

from pyOFTools.geometry import SampledSurfaceAdapter


@pytest.fixture
def openfoam_case(tmp_path):
    """
    Create a minimal OpenFOAM case for testing.
    For actual testing, this should point to a real case like damBreak.
    """
    # In practice, we'll use an existing test case
    # This is a placeholder fixture
    import os

    case_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "example", "damBreak")
    if not os.path.exists(case_path):
        pytest.skip("damBreak example case not found")
    return case_path


@pytest.fixture
def runTime(openfoam_case):
    """Create OpenFOAM Time object."""
    args = argList(["solver", "-case", openfoam_case])
    return Time(args)


@pytest.fixture
def mesh(runTime):
    """Create OpenFOAM mesh."""
    return createMesh(runTime)


@pytest.fixture
def plane_surface(runTime, mesh):
    """Create a plane surface for testing."""
    surf_dict = dictionary()
    surf_dict.add("type", Word("plane"))
    surf_dict.add("source", Word("cells"))
    surf_dict.add("interpolate", True)

    # Plane definition
    point = vector(0.292, 0.0, 0.0)
    normal = vector(1.0, 0.0, 0.0)
    surf_dict.add("point", point)
    surf_dict.add("normal", normal)

    surface = sampledSurface.New(Word("testPlane"), mesh, surf_dict)
    surface.update()

    return surface


def test_sampled_surface_adapter_creation(plane_surface):
    """Test that we can create a SampledSurfaceAdapter."""
    adapter = SampledSurfaceAdapter(plane_surface)
    assert adapter is not None
    assert adapter._surface == plane_surface


def test_adapter_points(plane_surface):
    """Test that we can get points from the adapter."""
    adapter = SampledSurfaceAdapter(plane_surface)
    points = adapter.points

    assert points is not None
    assert len(points) > 0
    # Points should be a vectorField or array-like
    assert hasattr(points, "__len__")


def test_adapter_face_centers(plane_surface):
    """Test that we can get face centers from the adapter."""
    adapter = SampledSurfaceAdapter(plane_surface)
    centers = adapter.face_centers

    assert centers is not None
    assert len(centers) > 0


def test_adapter_face_areas(plane_surface):
    """Test that we can get face areas (vectors) from the adapter."""
    adapter = SampledSurfaceAdapter(plane_surface)
    areas = adapter.face_areas

    assert areas is not None
    assert len(areas) > 0


def test_adapter_face_area_magnitudes(plane_surface):
    """Test that we can get face area magnitudes."""
    adapter = SampledSurfaceAdapter(plane_surface)
    magnitudes = adapter.face_area_magnitudes

    assert magnitudes is not None
    assert len(magnitudes) > 0
    # All magnitudes should be positive
    assert all(m > 0 for m in magnitudes)


def test_adapter_total_area(plane_surface):
    """Test that we can get the total surface area."""
    adapter = SampledSurfaceAdapter(plane_surface)
    total_area = adapter.total_area

    assert total_area > 0
    # Total area should equal sum of magnitudes
    expected_total = sum(adapter.face_area_magnitudes)
    assert abs(total_area - expected_total) < 1e-10


def test_adapter_consistency(plane_surface):
    """Test that all geometric properties are consistent."""
    adapter = SampledSurfaceAdapter(plane_surface)

    # Number of face centers and face areas should match
    n_face_centers = len(adapter.face_centers)
    assert len(adapter.face_areas) == n_face_centers
    assert len(adapter.face_area_magnitudes) == n_face_centers


def test_adapter_protocol_compliance(plane_surface):
    """Test that the adapter satisfies the SurfaceMesh protocol."""

    adapter = SampledSurfaceAdapter(plane_surface)

    # Check that all required protocol methods/properties exist
    assert hasattr(adapter, "points")
    assert hasattr(adapter, "face_centers")
    assert hasattr(adapter, "face_areas")
    assert hasattr(adapter, "face_area_magnitudes")
    assert hasattr(adapter, "total_area")

    # All should be callable/accessible
    _ = adapter.points
    _ = adapter.face_centers
    _ = adapter.face_areas
    _ = adapter.face_area_magnitudes
    _ = adapter.total_area


@pytest.mark.parametrize(
    "point,normal",
    [
        ((0.292, 0.0, 0.0), (1.0, 0.0, 0.0)),  # x-normal plane
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),  # y-normal plane
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),  # z-normal plane
    ],
)
def test_adapter_different_planes(runTime, mesh, point, normal):
    """Test adapter with different plane orientations."""
    surf_dict = dictionary()
    surf_dict.set("type", Word("plane"))
    surf_dict.set("point", vector(*point))
    surf_dict.set("normal", vector(*normal))

    surface = sampledSurface.New(Word("testPlane"), mesh, surf_dict)
    surface.update()
    adapter = SampledSurfaceAdapter(surface)

    # Basic checks
    assert len(adapter.points) > 0
    assert adapter.total_area > 0
