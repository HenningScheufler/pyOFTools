"""
Shared fixtures for integration tests.
"""

import os
import pathlib
import subprocess

import pytest
from pybFoam import Time, fvMesh

from pyOFTools import examples_root


def _cube_dir() -> str:
    return str(examples_root() / "cube")


def _dump_logs(case_dir: str, label: str) -> None:
    for log in sorted(pathlib.Path(case_dir).glob("log.*")):
        print(f"\n===== {label}: {log.name} (tail) =====")
        try:
            tail = log.read_text(errors="replace").splitlines()[-80:]
            print("\n".join(tail))
        except OSError as exc:
            print(f"(could not read {log.name}: {exc})")


@pytest.fixture(scope="session")
def ensure_case_mesh():
    """Session-scoped: build the cube case mesh on first use, Allclean on teardown.

    Yields the case directory so dependents (``change_test_dir``) can chdir into
    it. Runs ``./Allrun`` only if ``constant/polyMesh`` is missing, so the cost
    is paid at most once per session.
    """
    case_dir = _cube_dir()
    mesh_dir = os.path.join(case_dir, "constant", "polyMesh")

    if not os.path.isdir(mesh_dir):
        result = subprocess.run(
            ["./Allrun"], capture_output=True, text=True, cwd=case_dir
        )
        if result.returncode != 0:
            print(f"\n===== ./Allrun stdout =====\n{result.stdout}")
            print(f"\n===== ./Allrun stderr =====\n{result.stderr}")
            _dump_logs(case_dir, "Allrun")
            raise subprocess.CalledProcessError(
                result.returncode,
                ["./Allrun"],
                output=result.stdout,
                stderr=result.stderr,
            )

    yield case_dir

    allclean = os.path.join(case_dir, "Allclean")
    if os.path.isfile(allclean):
        subprocess.run([allclean], cwd=case_dir, check=False)


@pytest.fixture(scope="function")
def change_test_dir(request, ensure_case_mesh):
    """Change to the cube case dir for OpenFOAM case access."""
    os.chdir(ensure_case_mesh)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture
def time_mesh(change_test_dir):
    """Create OpenFOAM mesh from test case."""
    time = Time(".", ".")
    mesh = fvMesh(time)
    return time, mesh
