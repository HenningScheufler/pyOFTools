"""Global pytest configuration and fixtures"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

# Import the patch before any tests run - this modifies pybFoam classes
# to automatically disable FPE trapping after OpenFOAM initialization
import pyOFTools.patch_pybfoam  # noqa: F401
from pyOFTools import examples_root

# Example cases that tests run blockMesh/solvers in and that need cleanup
# after the session (so CI and local runs leave no generated artifacts).
_GENERATED_CASES = ("cube", "damBreak")

_TIME_DIR_RE = re.compile(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$")


def _clean_case(case_dir: Path) -> None:
    """Remove generated time/polyMesh/processor artifacts from an OpenFOAM case.

    Mirrors ``cleanCase0``: keeps ``0.orig`` and ``system``/``constant`` inputs,
    drops timestep directories, ``constant/polyMesh``, ``processor*``,
    ``postProcessing``, and ``log.*`` files.
    """
    if not case_dir.is_dir():
        return

    allclean = case_dir / "Allclean"
    if allclean.is_file():
        result = subprocess.run(
            [str(allclean)], cwd=str(case_dir), capture_output=True, text=True
        )
        if result.returncode == 0:
            return
        # Fall through to the Python fallback if Allclean failed (e.g. no
        # WM_PROJECT_DIR in the environment).

    poly_mesh = case_dir / "constant" / "polyMesh"
    if poly_mesh.is_dir():
        shutil.rmtree(poly_mesh, ignore_errors=True)

    post_processing = case_dir / "postProcessing"
    if post_processing.is_dir():
        shutil.rmtree(post_processing, ignore_errors=True)

    for entry in case_dir.iterdir():
        name = entry.name
        if entry.is_dir():
            if name == "0.orig":
                continue
            if name.startswith("processor") or _TIME_DIR_RE.match(name):
                shutil.rmtree(entry, ignore_errors=True)
        elif entry.is_file() and name.startswith("log."):
            entry.unlink(missing_ok=True)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(request):
    """
    Setup test environment at the start of the test session.

    The import of patch_pybfoam above ensures that pybFoam classes are
    patched to disable FPE trapping, preventing crashes when NumPy/pandas
    are used after OpenFOAM initialization.

    After the session, time directories, ``constant/polyMesh``, ``processor*``,
    ``postProcessing`` and ``log.*`` files generated under the example cases
    are removed. Pass ``--no-clean-up`` to keep them for debugging.
    """
    yield

    if not request.config.getoption("--no-clean-up"):
        return

    try:
        root = examples_root()
    except FileNotFoundError:
        return

    for case in _GENERATED_CASES:
        _clean_case(root / case)
