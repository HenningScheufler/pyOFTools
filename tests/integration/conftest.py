"""
Shared fixtures for integration tests.
"""

import os

import pytest
from pybFoam import Time, fvMesh


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def time_mesh(change_test_dir):
    """Create OpenFOAM mesh from test case."""
    time = Time(".", ".")
    mesh = fvMesh(time)
    return time, mesh
