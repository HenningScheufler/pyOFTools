"""
Tests for the SurfaceInterpolator class.
"""

import os
import pathlib
import subprocess

import pytest
from pybFoam import (
    Time,
    fvMesh,
    volScalarField,
    volVectorField,
)

from pyOFTools import examples_root
from pyOFTools.interpolation import SurfaceInterpolator, create_interpolated_dataset
from pyOFTools.surfaces import create_plane


def _ensure_case_mesh(case_dir: str) -> None:
    """Run Allrun in case_dir if constant/polyMesh is missing."""
    if os.path.isdir(os.path.join(case_dir, "constant", "polyMesh")):
        return
    result = subprocess.run(["./Allrun"], capture_output=True, text=True, cwd=case_dir)
    if result.returncode != 0:
        print(f"\n===== ./Allrun stdout =====\n{result.stdout}")
        print(f"\n===== ./Allrun stderr =====\n{result.stderr}")
        for log in sorted(pathlib.Path(case_dir).glob("log.*")):
            try:
                tail = "\n".join(log.read_text(errors="replace").splitlines()[-80:])
                print(f"\n===== {log.name} (tail) =====\n{tail}")
            except OSError as exc:
                print(f"(could not read {log.name}: {exc})")
        raise subprocess.CalledProcessError(
            result.returncode, ["./Allrun"], output=result.stdout, stderr=result.stderr
        )


@pytest.fixture
def openfoam_case():
    """Path to the damBreak example case, with mesh built on first use."""
    case_path = str(examples_root() / "damBreak")
    if not os.path.exists(case_path):
        pytest.skip("damBreak example case not found")
    _ensure_case_mesh(case_path)
    return case_path


@pytest.fixture
def runTime(openfoam_case):
    """Create OpenFOAM Time object pointing at the damBreak case."""
    original_dir = os.getcwd()
    os.chdir(openfoam_case)
    try:
        time = Time(".", ".")
        yield time
    finally:
        os.chdir(original_dir)


@pytest.fixture
def mesh(runTime):
    """Create OpenFOAM mesh."""
    return fvMesh(runTime)


@pytest.fixture
def plane_dataset(mesh):
    """A cutting-plane SurfaceDataSet through the damBreak mid-plane."""
    return create_plane(
        name="testPlane",
        mesh=mesh,
        point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )


@pytest.fixture
def plane_surface(plane_dataset):
    """The underlying ``sampledSurface`` of the plane dataset."""
    return plane_dataset.geometry._surface


def test_interpolator_creation_default_scheme():
    """Default-constructed interpolator uses cellPoint, face values."""
    interpolator = SurfaceInterpolator()
    assert interpolator.scheme == "cellPoint"
    assert interpolator.use_point_data is False


def test_interpolator_creation_with_scheme():
    interpolator = SurfaceInterpolator(scheme="cell")
    assert interpolator.scheme == "cell"


def test_interpolator_use_point_data_flag():
    interpolator = SurfaceInterpolator(scheme="cellPoint", use_point_data=True)
    assert interpolator.use_point_data is True


@pytest.mark.parametrize("scheme", ["cell", "cellPoint", "cellPointFace"])
def test_interpolator_valid_schemes(scheme, mesh, plane_surface):
    """All three documented schemes should be accepted and produce a field."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator(scheme=scheme)
    result = interpolator.interpolate(field, plane_surface)
    assert result is not None
    assert len(result) > 0


def test_interpolate_scalar_field(mesh, plane_surface):
    """Interpolating a volScalarField returns one value per face."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator()
    result = interpolator.interpolate(field, plane_surface)
    assert len(result) == len(plane_surface.Cf())


def test_interpolate_vector_field(mesh, plane_surface):
    """Interpolating a volVectorField returns one vector per face."""
    field = volVectorField.read_field(mesh, "U")
    interpolator = SurfaceInterpolator()
    result = interpolator.interpolate(field, plane_surface)
    assert len(result) == len(plane_surface.Cf())


def test_interpolate_to_points(mesh, plane_surface):
    """use_point_data=True interpolates onto surface points, not faces."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator(use_point_data=True)
    result = interpolator.interpolate(field, plane_surface)
    assert len(result) == len(plane_surface.points())


def test_interpolate_with_different_schemes(mesh, plane_surface):
    """Different schemes produce same-length, non-None results."""
    field = volScalarField.read_field(mesh, "p")
    result_cell = SurfaceInterpolator(scheme="cell").interpolate(field, plane_surface)
    result_cp = SurfaceInterpolator(scheme="cellPoint").interpolate(field, plane_surface)
    assert len(result_cell) == len(result_cp)


def test_create_interpolated_dataset(mesh, plane_surface):
    """create_interpolated_dataset wraps interpolator output as a SurfaceDataSet."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator()
    dataset = create_interpolated_dataset(field, plane_surface, interpolator, name="pressure")
    assert dataset.name == "pressure"
    assert dataset.field is not None
    assert len(dataset.field) == len(plane_surface.Cf())


def test_create_interpolated_dataset_default_name(mesh, plane_surface):
    """If no name is passed, the dataset takes the field's own name."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator()
    dataset = create_interpolated_dataset(field, plane_surface, interpolator)
    assert dataset.name == "p"


def test_create_interpolated_dataset_to_points(mesh, plane_surface):
    """Interpolator with use_point_data=True yields a per-point field."""
    field = volScalarField.read_field(mesh, "p")
    interpolator = SurfaceInterpolator(use_point_data=True)
    dataset = create_interpolated_dataset(field, plane_surface, interpolator, name="p_pts")
    assert len(dataset.field) == len(plane_surface.points())


def test_interpolator_multiple_fields(mesh, plane_surface):
    """A single interpolator handles different field types via dispatch."""
    interpolator = SurfaceInterpolator()
    p = volScalarField.read_field(mesh, "p")
    U = volVectorField.read_field(mesh, "U")
    assert len(interpolator.interpolate(p, plane_surface)) == len(plane_surface.Cf())
    assert len(interpolator.interpolate(U, plane_surface)) == len(plane_surface.Cf())


def test_interpolate_field_consistency(mesh, plane_surface):
    """Face- vs point-mode lengths match the surface's faces / points."""
    field = volScalarField.read_field(mesh, "p")
    faces = SurfaceInterpolator(use_point_data=False).interpolate(field, plane_surface)
    points = SurfaceInterpolator(use_point_data=True).interpolate(field, plane_surface)
    assert len(faces) == len(plane_surface.Cf())
    assert len(points) == len(plane_surface.points())
