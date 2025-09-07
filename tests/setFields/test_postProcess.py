import pytest

# import pandas as pd
import pybFoam
from pybFoam import fvMesh, Time, volScalarField, volVectorField, write
import sys
import os
import numpy as np


@pytest.fixture(scope="function")
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture(scope="function")
def mesh_and_time():
    argList = pybFoam.argList(["."])
    runTime = Time(argList)
    mesh = fvMesh(runTime)
    return mesh, runTime, argList


def test_post_process(change_test_dir, mesh_and_time):
    mesh, runTime, argList = mesh_and_time

    p = volScalarField.read_field(mesh, "p")
    U = volVectorField.read_field(mesh, "U")

    np_p = np.asarray(p.internalField())
    np_p[:] = 1e5

    nCells = mesh.nCells()

    selected_cells = np.array([True] * nCells)
    assert selected_cells[0]
    cell_center = mesh.C()

    for i, cc in enumerate(cell_center["internalField"]):
        if pybFoam.mag(cc) < 0.5:
            selected_cells[i] = False

    print(f"Selected cells: {np.sum(selected_cells)} out of {nCells}")

    np_p = np.asarray(p.internalField())

    assert np_p[0] == 1e5

    magC = pybFoam.mag(cell_center).internalField()

    mask = np.asarray(magC) < 0.5
    np_p[:] = np.where(mask, 1e5, 2e5)

    assert np_p[0] == 1e5
    assert np_p[-1] == 2e5

    assert p.internalField()[0] == 1e5
    assert p.internalField()[nCells - 1] == 2e5

    write(p)
