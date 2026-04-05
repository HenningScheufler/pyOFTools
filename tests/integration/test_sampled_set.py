import os

import numpy as np
import pytest
from pybFoam import (
    volScalarField,
)

from pyOFTools.datasets import PointDataSet
from pyOFTools.sets import (
    create_circle_set,
    create_cloud_set,
    create_polyline_set,
    create_uniform_set,
)


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


def test_uniformSet(time_mesh):
    """Test creation, geometry properties and distance calculation of uniform sampledSet."""

    # time needs to be returned to keep alive
    time, mesh = time_mesh

    # Create a simple field for testing
    p = volScalarField.read_field(mesh, "p")

    # Create a uniform set along x-axis through the cube mesh (spans -0.25 to 0.25)
    dataset = create_uniform_set(
        mesh=mesh,
        name="testLine",
        start=(-0.2, 0.0, 0.0),
        end=(0.2, 0.0, 0.0),
        n_points=50,
        field=p,
        axis="distance",
    )

    # Test basic properties
    assert dataset is not None
    assert isinstance(dataset, PointDataSet)
    assert dataset.name == "testLine"

    # Test geometry accessors
    geometry = dataset.geometry
    positions = geometry.positions
    distance = geometry.distance

    # Test field values
    field_values = dataset.field

    num_points = len(positions)
    assert num_points > 0
    assert len(distance) == num_points
    assert len(field_values) == num_points

    # Test distance properties
    distance_array = np.asarray(distance)

    # First point should be at distance ~0
    assert distance_array[0] == pytest.approx(0.0, abs=1e-6)

    # Last point should be at distance ~0.4 (length of line from -0.2 to 0.2)
    assert distance_array[-1] == pytest.approx(0.4, abs=1e-2)

    # Distance should be monotonically increasing
    for i in range(1, len(distance_array)):
        assert distance_array[i] > distance_array[i - 1]

    # Test positions are along the line from (-0.2,0,0) to (0.2,0,0)
    positions_array = np.asarray(positions)

    # Check that x-coordinates span the expected range
    x_coords = positions_array[:, 0]
    assert x_coords[0] == pytest.approx(-0.2, abs=1e-2)
    assert x_coords[-1] == pytest.approx(0.2, abs=1e-2)

    # Check that y and z coordinates remain close to 0
    y_coords = positions_array[:, 1]
    z_coords = positions_array[:, 2]
    assert np.allclose(y_coords, 0.0, atol=1e-2)
    assert np.allclose(z_coords, 0.0, atol=1e-2)

    # Test that field values are reasonable
    field_array = np.asarray(field_values)
    assert np.allclose(field_array, 0.0)


def test_cloudSet(time_mesh):
    """Test creation and properties of cloud sampledSet."""

    time, mesh = time_mesh
    p = volScalarField.read_field(mesh, "p")

    # Create a cloud set with specific probe locations
    probe_points = [
        (-0.1, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.1, 0.0, 0.0),
        (0.0, -0.1, 0.0),
        (0.0, 0.1, 0.0),
    ]

    dataset = create_cloud_set(mesh=mesh, name="probes", points=probe_points, field=p, axis="xyz")

    # Test basic properties
    assert dataset is not None
    assert isinstance(dataset, PointDataSet)
    assert dataset.name == "probes"

    # Test geometry
    geometry = dataset.geometry
    positions = geometry.positions
    distance = geometry.distance
    field_values = dataset.field

    # Number of points should match or be less than requested (some may be outside mesh)
    num_points = len(positions)
    assert num_points > 0
    assert num_points <= len(probe_points)
    assert len(distance) == num_points
    assert len(field_values) == num_points

    # Verify positions are close to requested points (for valid points)
    positions_array = np.asarray(positions)
    for i, pos in enumerate(positions_array):
        # Each position should be close to one of the probe points
        min_dist = min(np.linalg.norm(pos - np.array(pp)) for pp in probe_points)
        assert min_dist < 0.1, f"Position {i} not close to any probe point"


def test_polylineSet(time_mesh):
    """Test creation and properties of polyline sampledSet."""

    time, mesh = time_mesh
    p = volScalarField.read_field(mesh, "p")

    # Create an L-shaped polyline
    knot_points = [
        (-0.15, -0.15, 0.0),  # Start
        (0.15, -0.15, 0.0),  # Corner
        (0.15, 0.15, 0.0),  # End
    ]

    dataset = create_polyline_set(
        mesh=mesh, name="Lpath", points=knot_points, n_points=60, field=p, axis="distance"
    )

    # Test basic properties
    assert dataset is not None
    assert isinstance(dataset, PointDataSet)
    assert dataset.name == "Lpath"

    # Test geometry
    geometry = dataset.geometry
    positions = geometry.positions
    distance = geometry.distance
    field_values = dataset.field

    num_points = len(positions)
    assert num_points > 0
    assert len(distance) == num_points
    assert len(field_values) == num_points

    # Test distance properties
    distance_array = np.asarray(distance)
    assert distance_array[0] == pytest.approx(0.0, abs=1e-6)

    # Distance should be monotonically increasing
    for i in range(1, len(distance_array)):
        assert distance_array[i] > distance_array[i - 1]

    # Total distance should be the sum of two segments
    # Just verify it's reasonable (not checking exact value due to sampling)
    assert distance_array[-1] > 0.5, "Total path length should be reasonable"
    assert distance_array[-1] < 3.0, "Total path length should not be excessive"

    # Verify positions follow the L-shape pattern
    positions_array = np.asarray(positions)

    # First point should be near start
    assert np.linalg.norm(positions_array[0] - np.array(knot_points[0])) < 0.05

    # Last point should be near end
    assert np.linalg.norm(positions_array[-1] - np.array(knot_points[2])) < 0.05


def test_circleSet(time_mesh):
    """Test creation and properties of circle sampledSet."""

    time, mesh = time_mesh
    p = volScalarField.read_field(mesh, "p")

    # Create a horizontal circle in the xy-plane
    origin = (0.0, 0.0, 0.0)
    circle_axis = (0.0, 0.0, 1.0)  # Normal to xy-plane
    start_point = (0.15, 0.0, 0.0)  # Radius = 0.15

    dataset = create_circle_set(
        mesh=mesh,
        name="circle",
        origin=origin,
        circle_axis=circle_axis,
        start_point=start_point,
        field=p,
        d_theta=15.0,  # 15 degree increments
        axis="distance",
    )

    # Test basic properties
    assert dataset is not None
    assert isinstance(dataset, PointDataSet)
    assert dataset.name == "circle"

    # Test geometry
    geometry = dataset.geometry
    positions = geometry.positions
    distance = geometry.distance
    field_values = dataset.field

    num_points = len(positions)
    assert num_points > 0
    assert len(distance) == num_points
    assert len(field_values) == num_points

    # Test distance properties
    distance_array = np.asarray(distance)
    assert distance_array[0] == pytest.approx(0.0, abs=1e-6)

    # Distance should be monotonically increasing
    for i in range(1, len(distance_array)):
        assert distance_array[i] >= distance_array[i - 1]

    # Verify positions are roughly circular
    positions_array = np.asarray(positions)
    origin_array = np.array(origin)

    # Calculate distances from origin for each point
    radii = []
    for pos in positions_array:
        # Distance from origin in xy-plane
        r = np.sqrt((pos[0] - origin_array[0]) ** 2 + (pos[1] - origin_array[1]) ** 2)
        radii.append(r)

    # All radii should be approximately equal to 0.15
    radii_array = np.array(radii)
    valid_radii = radii_array[radii_array > 0.01]  # Filter out invalid points
    if len(valid_radii) > 0:
        assert np.allclose(valid_radii, 0.15, atol=0.02), (
            "Points should lie on circle of radius 0.15"
        )

    # Check z-coordinates remain close to 0 (circle in xy-plane)
    z_coords = positions_array[:, 2]
    assert np.allclose(z_coords, 0.0, atol=1e-2)
