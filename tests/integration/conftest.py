"""
Shared fixtures for integration tests.
"""

import os
import pathlib
import subprocess

import pytest
from pybFoam import Time, fvMesh


def _ensure_cube_mesh():
    """Run Allrun for cube case if mesh doesn't exist."""
    cube_dir = os.path.join(os.path.dirname(__file__), "cube")
    mesh_dir = os.path.join(cube_dir, "constant", "polyMesh")
    if not os.path.isdir(mesh_dir):
        result = subprocess.run(
            ["./Allrun"], capture_output=True, text=True, cwd=cube_dir
        )
        if result.returncode != 0:
            print(f"\n===== ./Allrun stdout =====\n{result.stdout}")
            print(f"\n===== ./Allrun stderr =====\n{result.stderr}")
            for log in sorted(pathlib.Path(cube_dir).glob("log.*")):
                print(f"\n===== {log.name} (tail) =====")
                try:
                    tail = log.read_text(errors="replace").splitlines()[-80:]
                    print("\n".join(tail))
                except OSError as exc:
                    print(f"(could not read {log.name}: {exc})")
            raise subprocess.CalledProcessError(
                result.returncode, ["./Allrun"], output=result.stdout, stderr=result.stderr
            )


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    _ensure_cube_mesh()
    os.chdir(os.path.join(request.fspath.dirname, "cube"))
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def time_mesh(change_test_dir):
    """Create OpenFOAM mesh from test case."""
    time = Time(".", ".")
    mesh = fvMesh(time)
    return time, mesh
