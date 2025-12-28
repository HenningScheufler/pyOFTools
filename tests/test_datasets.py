import numpy as np
from pybFoam import boolList, labelList, scalarField

from pyOFTools.datasets import InternalDataSet, PatchDataSet, SurfaceDataSet


class DummyMesh:
    @property
    def positions(self):
        return np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


def test_internal_field_creation():
    mask = boolList([True, False, True])
    zones = labelList([1, 2, 1])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummyMesh()
    f = InternalDataSet(
        name="internal",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "internal"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummyMesh)


def test_patch_field_creation():
    mask = boolList([False, True])
    zones = labelList([0, 1])
    field = scalarField([1.0, 2.0])
    geometry = DummyMesh()
    f = PatchDataSet(
        name="patch",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "patch"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummyMesh)


def test_surface_field_creation():
    mask = boolList([True, True, False])
    zones = labelList([2, 2, 3])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummyMesh()
    f = SurfaceDataSet(
        name="surface",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "surface"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummyMesh)
