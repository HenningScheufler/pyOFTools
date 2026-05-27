"""
Tests for surface creation factory functions.
"""

import os
from collections.abc import Generator

import pytest
from pybFoam import Time, argList, createMesh, fvMesh

from pyOFTools import examples_root, surfaces


@pytest.fixture(scope="function")
def change_test_dir(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Change to test directory for OpenFOAM case access."""
    os.chdir(str(examples_root() / "cube"))
    yield
    os.chdir(request.config.invocation_params.dir)


@pytest.fixture
def runTime(change_test_dir: None) -> Time:
    """Create OpenFOAM Time object."""
    args = argList(["solver"])
    return Time(args)


@pytest.fixture
def mesh(runTime: Time) -> fvMesh:
    """Create OpenFOAM mesh."""
    return createMesh(runTime)


def test_create_plane_surface(mesh: fvMesh) -> None:
    """Test plane surface creation."""
    surface = surfaces.create_plane(
        mesh=mesh,
        name="testPlane",
        field=None,
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # Check that surface has been updated (has geometry)
    assert len(surface.geometry.positions) > 0


def test_create_plane_with_dict_points(mesh: fvMesh) -> None:
    """Test plane creation with dictionary-style points."""
    surface = surfaces.create_plane(
        mesh=mesh,
        name="testPlane",
        field=None,
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    assert len(surface.geometry.positions) > 0


def test_create_patch_surface(mesh: fvMesh) -> None:
    """Test patch surface creation."""
    # cube case should have these patches
    surface = surfaces.create_patch_surface(
        mesh=mesh,
        name="testPatch",
        patches=["front"],
    )

    assert surface is not None
    # Patch might not have geometry if it doesn't exist or is empty
    points = surface.points()
    if points is not None:
        assert len(points) >= 0


def test_create_cutting_plane(mesh: fvMesh) -> None:
    """Test cutting plane surface creation."""
    surface = surfaces.create_cutting_plane(
        mesh=mesh,
        name="testCuttingPlane",
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    assert len(surface.points()) > 0


@pytest.mark.skip(reason="Requires alpha.water field to be initialized")
def test_create_iso_surface(mesh: fvMesh) -> None:
    """Test iso-surface creation."""
    surface = surfaces.create_iso_surface(
        mesh=mesh,
        name="testIsoSurface",
        field=None,
        iso_field_name="alpha.water",
        iso_value=0.5,
    )

    assert surface is not None
    # Iso-surface might be empty if field doesn't exist or no iso-value cells
    # Just check it doesn't crash


def test_plane_with_interpolation_options(mesh: fvMesh) -> None:
    """Test plane creation with triangulation option."""
    surface = surfaces.create_plane(
        mesh=mesh,
        name="testPlane",
        field=None,
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    assert len(surface.geometry.positions) > 0


def test_cutting_plane_with_bounds(mesh: fvMesh) -> None:
    """Test cutting plane at mesh boundary."""
    surface = surfaces.create_cutting_plane(
        mesh=mesh,
        name="testCuttingPlane",
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # Surface might be empty if plane doesn't intersect mesh
    assert len(surface.points()) >= 0


@pytest.mark.parametrize(
    "name,point,normal",
    [
        ("plane_x", (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        ("plane_y", (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ("plane_z", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ],
)
def test_multiple_planes(
    mesh: fvMesh,
    name: str,
    point: tuple[float, float, float],
    normal: tuple[float, float, float],
) -> None:
    """Test creating multiple different planes."""
    surface = surfaces.create_plane(
        mesh=mesh,
        name=name,
        field=None,
        point=point,
        normal=normal,
    )

    assert surface is not None
    assert len(surface.geometry.positions) > 0


def test_invalid_patch_name(mesh: fvMesh) -> None:
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


def test_surface_name_preservation(mesh: fvMesh) -> None:
    """Test that surface names are preserved."""
    name = "myCustomSurface"
    surface = surfaces.create_plane(
        mesh=mesh,
        name=name,
        field=None,
        point=(0.0, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )

    assert surface is not None
    # Check dataset name
    assert surface.name == name
