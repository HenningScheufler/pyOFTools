"""Unit tests for the Python API of the pythonMixed boundary condition."""

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pytest

from pyOFTools.bc import MixedBC, ScalarMixed, _create, _evaluate


class Inflow(MixedBC):
    Tmean: float
    amplitude: float = 10
    steps: int = 1
    active: bool = True
    label: str = "a"

    def update(self) -> ScalarMixed:
        return ScalarMixed(
            refValue=self.Tmean + self.amplitude * self.time,
            valueFraction=(self.phi < 0).astype(float),
        )


class Returns(MixedBC):
    result = None

    def update(self) -> Any:
        return self.result


def evaluate(bc: MixedBC, phi: Optional[list[float]] = None, time: float = 2.0) -> Any:
    n = 2 if phi is None else len(phi)
    Sf = np.tile([2.0, 0.0, 0.0], (n, 1))
    return _evaluate(
        bc, time, np.zeros((n, 3)), Sf, np.full(n, 2.0), None if phi is None else np.array(phi)
    )


def test_defaults_are_fixed_value() -> None:
    coeffs = ScalarMixed(refValue=300.0)
    assert (coeffs.refGrad, coeffs.valueFraction) == (0.0, 1.0)


def test_parameters_are_converted_from_dictionary_strings() -> None:
    bc = Inflow(Tmean="300", amplitude="2.5", steps="3", active="off", label='"hot"')
    assert (bc.Tmean, bc.amplitude, bc.steps, bc.active, bc.label) == (300.0, 2.5, 3, False, "hot")


def test_optional_parameter_uses_class_default() -> None:
    assert Inflow(Tmean=1).amplitude == 10


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({}, "missing parameter 'Tmean'"),
        ({"Tmean": 1, "typo": 2}, "unknown parameters"),
        ({"Tmean": "hot"}, "Parameter 'Tmean' expects float"),
        ({"Tmean": 1, "active": "maybe"}, "Parameter 'active' expects bool"),
    ],
)
def test_invalid_parameters_raise(params: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Inflow(**params)


def test_evaluate_expands_scalars_and_applies_flux_direction() -> None:
    ref_value, ref_grad, fraction = evaluate(Inflow(Tmean=300, amplitude=1), [-1.0, 1.0])
    np.testing.assert_array_equal(ref_value, [302.0, 302.0])
    np.testing.assert_array_equal(ref_grad, [0.0, 0.0])
    np.testing.assert_array_equal(fraction, [1.0, 0.0])


def test_geometry_is_exposed() -> None:
    bc = Inflow(Tmean=1)
    evaluate(bc, [-1.0])
    assert bc.size == 1
    assert bc.time == 2.0
    np.testing.assert_array_equal(bc.nf, [[1.0, 0.0, 0.0]])


def test_empty_patch_is_supported() -> None:
    ref_value, ref_grad, fraction = evaluate(Inflow(Tmean=300), [])
    assert ref_value.size == ref_grad.size == fraction.size == 0


def test_missing_phi_raises() -> None:
    with pytest.raises(RuntimeError, match="No 'phi' field"):
        evaluate(Inflow(Tmean=1))


@pytest.mark.parametrize(
    ("result", "error", "message"),
    [
        (1.0, TypeError, "must return ScalarMixed"),
        (ScalarMixed(refValue=np.ones(3)), ValueError, "refValue has shape"),
        (ScalarMixed(refValue=np.nan), ValueError, "NaN or infinite"),
        (ScalarMixed(refValue=1.0, valueFraction=1.5), ValueError, "between 0 and 1"),
    ],
)
def test_invalid_results_raise(result: Any, error: type[Exception], message: str) -> None:
    bc = Returns()
    bc.result = result
    with pytest.raises(error, match=message):
        evaluate(bc)


def test_create_loads_class_from_file(tmp_path: Path) -> None:
    file = tmp_path / "boundary.py"
    file.write_text(
        "from pyOFTools.bc import MixedBC, ScalarMixed\n"
        "class Fixed(MixedBC):\n"
        "    level: float\n"
        "    def update(self):\n"
        "        return ScalarMixed(refValue=self.level)\n"
    )
    bc = _create(str(file), "Fixed", {"level": "4"}, "inlet", "T")
    assert (bc.patch_name, bc.field_name) == ("inlet", "T")
    np.testing.assert_array_equal(evaluate(bc)[0], [4.0, 4.0])


def test_create_rejects_missing_file_and_wrong_class(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _create(str(tmp_path / "missing.py"), "A", {}, "inlet", "T")

    file = tmp_path / "other.py"
    file.write_text("class A:\n    pass\n")
    with pytest.raises(TypeError, match="derived from MixedBC"):
        _create(str(file), "A", {}, "inlet", "T")
