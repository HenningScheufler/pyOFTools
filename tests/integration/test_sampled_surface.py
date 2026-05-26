import os
from collections.abc import Iterator

import numpy as np
import pytest
from pybFoam import (
    Time,
    fvMesh,
    scalarField,
)

from pyOFTools import examples_root
from pyOFTools.geometry import SampledSurfaceAdapter
from pyOFTools.surfaces import create_plane


@pytest.fixture(scope="function")
def change_test_dir(request: pytest.FixtureRequest) -> Iterator[None]:
    """Change to test directory for OpenFOAM case access."""
    os.chdir(str(examples_root() / "cube"))
    yield
    os.chdir(request.config.invocation_params.dir)


def test_sampledPlane(change_test_dir: None, time_mesh: tuple[Time, fvMesh]) -> None:
    """Test creation, update, and geometry methods of sampledPlane surface."""

    # time needs to be returned to keep alive
    _, mesh = time_mesh

    surfData = create_plane(
        name="testPlane",
        mesh=mesh,
        field=scalarField([0.0]),  # Dummy field for testing
        point=(0.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
    )

    geom = surfData.geometry
    assert isinstance(geom, SampledSurfaceAdapter)
    plane = geom

    # assert plane is not None
    name = plane.name
    assert name == "testPlane"

    # Test geometry accessors
    Cf = plane.positions
    Sf = plane.face_areas
    magSf = plane.face_area_magnitudes

    num_faces = len(plane.face_areas)
    assert num_faces > 0
    assert len(Cf) == num_faces
    assert len(Sf) == num_faces

    # Test total area
    area = plane.total_area
    assert area == pytest.approx(0.25)

    # Verify area calculation matches sum of face areas
    assert np.isclose(0.25, np.sum(np.asarray(magSf)), rtol=1e-5)

    # Verify Sf magnitude equals magSf
    Sf_array = np.asarray(Sf)
    magSf_array = np.asarray(magSf)
    Sf_magnitude = np.linalg.norm(Sf_array, axis=1)
    assert np.allclose(Sf_magnitude, magSf_array, rtol=1e-10)
