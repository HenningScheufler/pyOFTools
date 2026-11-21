"""Run the pythonMixed example case with a real OpenFOAM solver."""

import math
import re
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from pyOFTools import clone_example


def _patch_block(text: str, patch: str) -> str:
    match = re.search(rf"^\s*{patch}\s*\{{(.*?)^\s*\}}", text, re.MULTILINE | re.DOTALL)
    assert match, f"patch {patch} not found"
    return match.group(1)


def _patch_value(text: str, patch: str) -> float:
    match = re.search(
        r"value\s+(?:uniform\s+|nonuniform List<scalar> 1\()([-+.\deE]+)", _patch_block(text, patch)
    )
    assert match, f"value of patch {patch} not found"
    return float(match.group(1))


def _internal_values(text: str) -> list[float]:
    match = re.search(r"internalField\s+nonuniform List<scalar>\s*\d+\s*\((.*?)\)", text, re.DOTALL)
    assert match, "internal field not found"
    return [float(value) for value in match.group(1).split()]


@pytest.fixture(scope="module")
def solved_case() -> Iterator[Path]:
    case = clone_example("pythonMixedBC")
    subprocess.run(["./Allrun"], cwd=case, check=True, capture_output=True, text=True)
    yield case
    shutil.rmtree(case.parent, ignore_errors=True)


def test_solver_completes(solved_case: Path) -> None:
    log = (solved_case / "log.scalarTransportFoam").read_text()
    assert "End" in log and "FOAM FATAL" not in log


def test_inflow_uses_python_value(solved_case: Path) -> None:
    text = (solved_case / "1" / "T").read_text()
    assert _patch_value(text, "inlet") == pytest.approx(300 + 10 * math.sin(1.0), abs=1e-8)


def test_outflow_is_zero_gradient(solved_case: Path) -> None:
    text = (solved_case / "1" / "T").read_text()
    assert _patch_value(text, "outlet") == pytest.approx(_internal_values(text)[-1], abs=1e-8)


def test_written_field_keeps_input_entries(solved_case: Path) -> None:
    block = _patch_block((solved_case / "1" / "T").read_text(), "inlet")
    for entry in ("pythonMixed", "system/boundary.py", "HotInflow", "Tmean", "amplitude"):
        assert entry in block
