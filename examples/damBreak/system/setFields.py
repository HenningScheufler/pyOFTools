"""Initial conditions for the damBreak case, in Python.

Invoked by ``pyoftools setFields system/setFields.py``. Sets ``alpha.water``
to 1 inside a rectangular box (the water column) **and** inside a sphere at
the origin (a small inclusion that highlights how Box/Sphere compose).

Anything you can express with ``Box``, ``Sphere``, ``&``, ``|``, ``~`` from
:mod:`pyOFTools.spatial_selectors` you can use here — the same selector API
that drives in-situ post-processing later in the run.
"""

import numpy as np
import pybFoam
from pybFoam import volScalarField, write

from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from pyOFTools.spatial_selectors import Box, Sphere


def set_field(mesh):
    # ``read_field`` loads ``0/alpha.water`` from disk and registers it.
    alpha = volScalarField.read_field(mesh, "alpha.water")

    # ``np.asarray`` returns a zero-copy view of the OpenFOAM internalField;
    # in-place writes here mutate the underlying field that ``write(alpha)``
    # will persist below.
    np_alpha = np.asarray(alpha["internalField"])
    np_alpha[:] = 0.0  # start from a clean baseline

    # ``InternalDataSet`` wraps the field + mesh adapter into the dataset
    # shape selectors expect. ``mask`` (written by the selector below) and
    # ``groups`` (written by binners) live on this object.
    int_alpha = InternalDataSet(
        name="alpha.water",
        field=alpha["internalField"],
        geometry=FvMeshInternalAdapter(mesh),
    )

    # The water column (a box covering the lower-left corner) OR a sphere
    # centred at the origin. ``box | sphere`` builds a union selector; the
    # final mask is True wherever the cell centre is inside either region.
    box = Box(min=(0, 0, -1), max=(0.1461, 0.292, 1))
    sphere = Sphere(center=(0.0, 0.0, 0.0), radius=0.25)
    combined = box | sphere

    # ``compute`` evaluates the selector and writes ``int_alpha.mask`` —
    # one boolean per cell. No values are touched on the field itself.
    int_alpha = combined.compute(int_alpha)
    mask = np.asarray(int_alpha.mask)

    # Apply the mask: cells inside the region get α = 1, the rest stay 0.
    np_alpha[mask] = 1.0

    # Flush the mutated field back to ``0/alpha.water``.
    write(alpha)


# Standard OpenFOAM case-open boilerplate. ``argList(["."])`` treats the
# current directory as the case root; ``Time`` and ``fvMesh`` give us the
# clock and the polyMesh that ``blockMesh`` has already written.
argList = pybFoam.argList(["."])
runTime = pybFoam.Time(argList)
mesh = pybFoam.fvMesh(runTime)

set_field(mesh)
