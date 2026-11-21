"""Boundary conditions written in Python.

Select one in a field file with ``type pythonMixed;`` and derive the class from
:class:`MixedBC`. Annotated class attributes are read from the patch entry::

    class HotInflow(MixedBC):
        Tmean: float
        amplitude: float = 10

        def update(self) -> ScalarMixed:
            return ScalarMixed(
                refValue=self.Tmean + self.amplitude * np.sin(self.time),
                valueFraction=(self.phi < 0).astype(float),
            )
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, get_origin, get_type_hints

import numpy as np
from numpy.typing import NDArray

__all__ = ["MixedBC", "ScalarField", "ScalarMixed"]

ScalarField = float | NDArray[np.float64]

_TRUE = {"true", "yes", "on", "y", "t"}
_FALSE = {"false", "no", "off", "n", "f"}


@dataclass
class ScalarMixed:
    """Coefficients of a scalar mixed boundary condition.

    Each value is either a single number or an array with one value per face.
    A ``valueFraction`` of 1 fixes the value and 0 fixes the gradient.
    """

    refValue: ScalarField
    refGrad: ScalarField = 0.0
    valueFraction: ScalarField = 1.0


def _convert(name: str, value: Any, target: Any) -> Any:
    """Convert a dictionary entry to the annotated type of the parameter."""
    text = value.strip().strip('"') if isinstance(value, str) else value
    try:
        if target is bool:
            if isinstance(text, str):
                lowered = text.lower()
                if lowered in _TRUE:
                    return True
                if lowered in _FALSE:
                    return False
                raise ValueError(text)
            return bool(text)
        if target in (float, int, str):
            return target(text)
    except ValueError as err:
        raise ValueError(f"Parameter '{name}' expects {target.__name__}, got {value!r}") from err
    raise TypeError(f"Parameter '{name}' has unsupported type {target!r}")


class MixedBC:
    """Base class for Python mixed boundary conditions.

    Subclasses implement :meth:`update`, which runs on every ``updateCoeffs()``
    and therefore also during inner iterations. In parallel, each processor
    sees only its local faces, which may be none.
    """

    def __init__(self, **params: Any) -> None:
        hints = {
            name: hint
            for name, hint in get_type_hints(type(self)).items()
            if get_origin(hint) is not ClassVar
        }

        unknown = sorted(set(params) - set(hints))
        if unknown:
            raise ValueError(f"{type(self).__name__}: unknown parameters {unknown}")

        for name, hint in hints.items():
            if name in params:
                setattr(self, name, _convert(name, params[name], hint))
            elif not hasattr(type(self), name):
                raise ValueError(f"{type(self).__name__}: missing parameter '{name}'")

        self.patch_name = ""
        self.field_name = ""
        self._time = 0.0
        self._Cf: NDArray[np.float64] = np.empty((0, 3))
        self._Sf: NDArray[np.float64] = np.empty((0, 3))
        self._magSf: NDArray[np.float64] = np.empty(0)
        self._phi: NDArray[np.float64] | None = None

    def update(self) -> ScalarMixed:
        """Return the mixed coefficients for the current state."""
        raise NotImplementedError

    @property
    def time(self) -> float:
        """Current simulation time."""
        return self._time

    @property
    def size(self) -> int:
        """Number of faces on this processor."""
        return int(self._magSf.size)

    @property
    def Cf(self) -> NDArray[np.float64]:
        """Face centres, shape ``(n, 3)``."""
        return self._Cf

    @property
    def Sf(self) -> NDArray[np.float64]:
        """Outward face area vectors, shape ``(n, 3)``."""
        return self._Sf

    @property
    def magSf(self) -> NDArray[np.float64]:
        """Face areas, shape ``(n,)``."""
        return self._magSf

    @property
    def nf(self) -> NDArray[np.float64]:
        """Outward unit face normals, shape ``(n, 3)``."""
        return self._Sf / self._magSf[:, np.newaxis]

    @property
    def phi(self) -> NDArray[np.float64]:
        """Face flux, positive when leaving the domain."""
        if self._phi is None:
            raise RuntimeError(f"No 'phi' field available on patch '{self.patch_name}'")
        return self._phi


def _load_class(path: str, class_name: str) -> type[MixedBC]:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Python boundary condition file not found: {resolved}")

    digest = hashlib.sha1(str(resolved).encode()).hexdigest()[:12]
    module_name = f"_pyoftools_bc_{resolved.stem}_{digest}"

    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(module_name, resolved)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load Python file: {resolved}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[module_name]
            raise

    cls = getattr(module, class_name, None)
    if not (isinstance(cls, type) and issubclass(cls, MixedBC)):
        raise TypeError(f"'{class_name}' in {resolved} must be a class derived from MixedBC")
    return cls


def _create(
    path: str, class_name: str, coeffs: dict[str, str], patch_name: str, field_name: str
) -> MixedBC:
    """Create a boundary condition. Called from C++."""
    bc = _load_class(path, class_name)(**coeffs)
    bc.patch_name = patch_name
    bc.field_name = field_name
    return bc


def _face_values(name: str, value: Any, size: int) -> NDArray[np.float64]:
    """Return ``value`` as a new float array with one entry per face."""
    array = np.asarray(value, dtype=np.float64)
    if array.ndim == 0:
        result = np.full(size, float(array))
    elif array.shape == (size,):
        result = array.copy()
    else:
        raise ValueError(f"{name} has shape {array.shape}, expected a scalar or ({size},)")

    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} contains NaN or infinite values")
    return result


def _evaluate(
    bc: MixedBC,
    time: float,
    Cf: NDArray[np.float64],
    Sf: NDArray[np.float64],
    magSf: NDArray[np.float64],
    phi: NDArray[np.float64] | None,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Run ``bc.update()`` and validate the result. Called from C++."""
    # The inputs are views of OpenFOAM data, so user code gets its own copies
    bc._time = float(time)
    bc._Cf = np.array(Cf, dtype=np.float64)
    bc._Sf = np.array(Sf, dtype=np.float64)
    bc._magSf = np.array(magSf, dtype=np.float64)
    bc._phi = None if phi is None else np.array(phi, dtype=np.float64)

    result = bc.update()
    if not isinstance(result, ScalarMixed):
        raise TypeError(
            f"{type(bc).__name__}.update() must return ScalarMixed, got {type(result).__name__}"
        )

    size = bc.size
    ref_value = _face_values("refValue", result.refValue, size)
    ref_grad = _face_values("refGrad", result.refGrad, size)
    fraction = _face_values("valueFraction", result.valueFraction, size)

    if np.any((fraction < 0) | (fraction > 1)):
        raise ValueError("valueFraction must be between 0 and 1")

    return ref_value, ref_grad, fraction
