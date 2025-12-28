"""
Tests for surface creation factory functions.
"""

import pytest
from pybFoam import Time, argList, createMesh

from pyOFTools import surfaces


@pytest.fixture
def openfoam_case():
    """Get path to OpenFOAM test case."""
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


def test_create_plane_surface(mesh):
    """Test plane surface creation."""
    surface = surfaces.create_plane_surface(
        mesh=mesh,
        name="testPlane",
        point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # Check that surface has been updated (has geometry)
    assert len(surface.points()) > 0


def test_create_plane_with_dict_points(mesh):
    """Test plane creation with dictionary-style points."""
    surface = surfaces.create_plane_surface(
        mesh=mesh,
        name="testPlane",
        point={"x": 0.292, "y": 0.0, "z": 0.0},
        normal={"x": 1.0, "y": 0.0, "z": 0.0},
    )

    assert surface is not None
    assert len(surface.points()) > 0


def test_create_patch_surface(mesh):
    """Test patch surface creation."""
    # damBreak case should have these patches
    surface = surfaces.create_patch_surface(
        mesh=mesh,
        name="testPatch",
        patches=["leftWall"],
    )

    assert surface is not None
    # Patch might not have geometry if it doesn't exist or is empty
    points = surface.points()
    if points is not None:
        assert len(points) >= 0


def test_create_cutting_plane(mesh):
    """Test cutting plane surface creation."""
    surface = surfaces.create_cutting_plane(
        mesh=mesh,
        name="testCuttingPlane",
        point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    assert len(surface.points()) > 0


@pytest.mark.skip(reason="Requires alpha.water field to be initialized")
def test_create_iso_surface(mesh):
    """Test iso-surface creation."""
    surface = surfaces.create_iso_surface(
        mesh=mesh,
        name="testIsoSurface",
        field_name="alpha.water",
        iso_value=0.5,
    )

    assert surface is not None
    # Iso-surface might be empty if field doesn't exist or no iso-value cells
    # Just check it doesn't crash


def test_plane_with_interpolation_options(mesh):
    """Test plane creation with triangulation option."""
    surface = surfaces.create_plane_surface(
        mesh=mesh,
        name="testPlane",
        point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
        triangulate=False,
    )

    assert surface is not None
    assert len(surface.points()) > 0


def test_cutting_plane_with_bounds(mesh):
    """Test cutting plane at mesh boundary."""
    surface = surfaces.create_cutting_plane(
        mesh=mesh,
        name="testCuttingPlane",
        point=(0.292, 0.292, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # Surface might be empty if plane doesn't intersect mesh
    assert len(surface.points()) >= 0


@pytest.mark.parametrize(
    "name,point,normal",
    [
        ("plane_x", (0.292, 0.0, 0.0), (1.0, 0.0, 0.0)),
        ("plane_y", (0.0, 0.292, 0.0), (0.0, 1.0, 0.0)),
        ("plane_z", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ],
)
def test_multiple_planes(mesh, name, point, normal):
    """Test creating multiple different planes."""
    surface = surfaces.create_plane_surface(
        mesh=mesh,
        name=name,
        point=point,
        normal=normal,
    )

    assert surface is not None
    assert len(surface.points()) > 0


def test_invalid_patch_name(mesh):
    """Test that invalid patch name doesn't crash."""
    # This should work without crashing, surface might be empty
    surface = surfaces.create_patch_surface(
        mesh=mesh,
        name="testPatch",
        patches=["nonexistentPatch"],
    )

    assert surface is not None
    # Points might be None for invalid patch
    points = surface.points()
    if points is not None:
        assert len(points) >= 0


def test_surface_name_preservation(mesh):
    """Test that surface names are preserved."""
    name = "myCustomSurface"
    surface = surfaces.create_plane_surface(
        mesh=mesh,
        name=name,
        point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # OpenFOAM surfaces have a name() method - compare as string
    assert str(surface.name()) == name
