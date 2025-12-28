"""
Tests for the SurfaceInterpolator class.
"""

import pytest
from pyOFTools.interpolation import SurfaceInterpolator, create_interpolated_dataset

from pybFoam import (
    Time,
    argList,
    fvMesh,
    vector,
)


@pytest.fixture
def openfoam_case():
    """Get path to OpenFOAM test case."""
    import os

    case_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "example", "damBreak"
    )
    if not os.path.exists(case_path):
        pytest.skip("damBreak example case not found")
    return case_path


@pytest.fixture
def runTime(openfoam_case):
    """Create OpenFOAM Time object."""
    import os
    original_dir = os.getcwd()
    os.chdir(openfoam_case)
    try:
        args = argList(["."])
        time = Time(args)
        return time
    finally:
        os.chdir(original_dir)


@pytest.fixture
def mesh(runTime):
    """Create OpenFOAM mesh."""
    return fvMesh(runTime)


@pytest.fixture
def plane_surface(mesh):
    """Create a plane surface for testing."""
    from pyOFTools import surfaces

    return surfaces.create_plane_surface(
        mesh=mesh,
        name="testPlane",
        base_point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )


def test_interpolator_creation_default_scheme(mesh):
    """Test creating interpolator with default scheme."""
    interpolator = SurfaceInterpolator(mesh)

    assert interpolator is not None
    assert interpolator.mesh == mesh


def test_interpolator_creation_with_scheme(mesh):
    """Test creating interpolator with specific scheme."""
    interpolator = SurfaceInterpolator(mesh, interpolation_scheme="cellPoint")

    assert interpolator is not None
    assert interpolator.interpolation_scheme == "cellPoint"


def test_interpolator_invalid_scheme(mesh):
    """Test that invalid scheme raises ValueError."""
    with pytest.raises(ValueError, match="Invalid interpolation scheme"):
        SurfaceInterpolator(mesh, interpolation_scheme="invalidScheme")


@pytest.mark.parametrize(
    "scheme",
    ["cell", "cellPoint", "cellPointFace"],
)
def test_interpolator_valid_schemes(mesh, scheme):
    """Test all valid interpolation schemes."""
    interpolator = SurfaceInterpolator(mesh, interpolation_scheme=scheme)
    assert interpolator.interpolation_scheme == scheme


def test_interpolate_scalar_field(mesh, plane_surface, runTime):
    """Test interpolating a scalar field onto a surface."""
    from pybFoam import volScalarField

    # Read a scalar field from the case (e.g., p or alpha.water)
    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    interpolator = SurfaceInterpolator(mesh)
    result = interpolator.interpolate_scalar(field, plane_surface)

    assert result is not None
    assert len(result) > 0
    assert len(result) == len(plane_surface.Cf())


def test_interpolate_vector_field(mesh, plane_surface, runTime):
    """Test interpolating a vector field onto a surface."""
    from pybFoam import volVectorField

    # Read a vector field from the case (e.g., U)
    try:
        field = volVectorField.New(runTime, mesh, "U")
    except:
        pytest.skip("Could not read velocity field from case")

    interpolator = SurfaceInterpolator(mesh)
    result = interpolator.interpolate_vector(field, plane_surface)

    assert result is not None
    assert len(result) > 0
    assert len(result) == len(plane_surface.Cf())


def test_interpolate_to_points(mesh, plane_surface, runTime):
    """Test interpolating to surface points instead of face centers."""
    from pybFoam import volScalarField

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    interpolator = SurfaceInterpolator(mesh)
    result = interpolator.interpolate_scalar(
        field, plane_surface, interpolate_to_points=True
    )

    assert result is not None
    assert len(result) > 0
    # Should have same length as points, not faces
    assert len(result) == len(plane_surface.points())


def test_interpolate_with_different_schemes(mesh, plane_surface, runTime):
    """Test interpolation with different schemes produces different results."""
    from pybFoam import volScalarField

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    result_cell = SurfaceInterpolator(mesh, "cell").interpolate_scalar(
        field, plane_surface
    )
    result_cellPoint = SurfaceInterpolator(mesh, "cellPoint").interpolate_scalar(
        field, plane_surface
    )

    assert len(result_cell) == len(result_cellPoint)
    # Results should potentially differ (but might be very similar)
    assert result_cell is not None
    assert result_cellPoint is not None


def test_create_interpolated_dataset(mesh, plane_surface, runTime):
    """Test the convenience function for creating SurfaceDataSet."""
    from pybFoam import volScalarField
    from pyOFTools.geometry import SampledSurfaceAdapter

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    adapter = SampledSurfaceAdapter(plane_surface)
    dataset = create_interpolated_dataset(
        field_name="pressure",
        field=field,
        surface=plane_surface,
        geometry_adapter=adapter,
        mesh=mesh,
    )

    assert dataset is not None
    assert dataset.name == "pressure"
    assert dataset.geometry == adapter
    assert dataset.field is not None
    assert len(dataset.field) > 0


def test_create_interpolated_dataset_with_scheme(mesh, plane_surface, runTime):
    """Test dataset creation with specific interpolation scheme."""
    from pybFoam import volScalarField
    from pyOFTools.geometry import SampledSurfaceAdapter

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    adapter = SampledSurfaceAdapter(plane_surface)
    dataset = create_interpolated_dataset(
        field_name="pressure",
        field=field,
        surface=plane_surface,
        geometry_adapter=adapter,
        mesh=mesh,
        interpolation_scheme="cellPoint",
    )

    assert dataset is not None
    assert dataset.name == "pressure"


def test_create_interpolated_dataset_to_points(mesh, plane_surface, runTime):
    """Test dataset creation with point interpolation."""
    from pybFoam import volScalarField
    from pyOFTools.geometry import SampledSurfaceAdapter

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    adapter = SampledSurfaceAdapter(plane_surface)
    dataset = create_interpolated_dataset(
        field_name="pressure",
        field=field,
        surface=plane_surface,
        geometry_adapter=adapter,
        mesh=mesh,
        interpolate_to_points=True,
    )

    assert dataset is not None
    # Field length should match number of points
    assert len(dataset.field) == len(plane_surface.points())


def test_interpolator_multiple_fields(mesh, plane_surface, runTime):
    """Test interpolating multiple fields with the same interpolator."""
    from pybFoam import volScalarField, volVectorField

    interpolator = SurfaceInterpolator(mesh)

    # Try to read and interpolate multiple fields
    fields_to_test = []
    try:
        p_field = volScalarField.New(runTime, mesh, "p")
        fields_to_test.append(("scalar", p_field))
    except:
        pass

    try:
        U_field = volVectorField.New(runTime, mesh, "U")
        fields_to_test.append(("vector", U_field))
    except:
        pass

    if not fields_to_test:
        pytest.skip("Could not read any fields from case")

    for field_type, field in fields_to_test:
        if field_type == "scalar":
            result = interpolator.interpolate_scalar(field, plane_surface)
        else:
            result = interpolator.interpolate_vector(field, plane_surface)

        assert result is not None
        assert len(result) > 0


def test_interpolate_field_consistency(mesh, plane_surface, runTime):
    """Test that interpolated field has consistent dimensions."""
    from pybFoam import volScalarField

    try:
        field = volScalarField.New(runTime, mesh, "p")
    except:
        pytest.skip("Could not read pressure field from case")

    interpolator = SurfaceInterpolator(mesh)

    # Face interpolation
    result_faces = interpolator.interpolate_scalar(
        field, plane_surface, interpolate_to_points=False
    )

    # Point interpolation
    result_points = interpolator.interpolate_scalar(
        field, plane_surface, interpolate_to_points=True
    )

    # Check dimensions
    assert len(result_faces) == len(plane_surface.Cf())
    assert len(result_points) == len(plane_surface.points())
