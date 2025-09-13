import pybFoam
import numpy as np
from pybFoam import volScalarField, write
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from pyOFTools.spatial_selectors import Box, Sphere


def set_field(mesh):

    alpha = volScalarField.read_field(mesh, "alpha.water")
    np_alpha = np.asarray(alpha["internalField"])
    np_alpha[:] = 0.0

    int_alpha = InternalDataSet(
        name="alpha.water",
        field=alpha["internalField"],
        geometry=FvMeshInternalAdapter(mesh),
    )

    box = Box(min=(0, 0, -1), max=(0.1461, 0.292, 1))
    sphere = Sphere(center=(0.0, 0.0, 0.0), radius=0.25)
    combined = box | sphere
    int_alpha = combined.compute(int_alpha)
    mask = np.asarray(int_alpha.mask)
    np_alpha[mask] = 1.0
    write(alpha)

argList = pybFoam.argList(["."])
runTime = pybFoam.Time(argList)
mesh = pybFoam.fvMesh(runTime)

set_field(mesh)