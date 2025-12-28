import numpy as np
from pybFoam import scalarField
import pytest
from pyOFTools.datasets import InternalDataSet, PatchDataSet, SurfaceDataSet


class DummyMesh:
    @property
    def positions(self):
        return np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


def test_internal_field_creation():
    # mask = np.array([True, False, True])
    # zones = np.array([1, 2, 1])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummyMesh()
    dataset = InternalDataSet(
        name="field",
        field=field,
        geometry=geometry,
        # mask=mask,
        # zones=zones,
    )
    assert dataset.name == "field"
    assert dataset.mask == None
    assert dataset.groups == None
    assert dataset.field == field
    assert isinstance(dataset.geometry, DummyMesh)
