"""
Shared fixtures for integration tests.
"""

import os

import pytest
from pybFoam import Time, fvMesh, volScalarField


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


def create_time_mesh():
    """Create OpenFOAM mesh from test case and load fields into registry."""
    time = Time(".", ".")
    mesh = fvMesh(time)
    
    # Load fields into registry
    volScalarField.read_field(mesh, "alpha.water")
    volScalarField.read_field(mesh, "p")
    
    return time, mesh
