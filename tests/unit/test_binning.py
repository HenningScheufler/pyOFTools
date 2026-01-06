import numpy as np
from pybFoam import labelList, scalarField, vectorField

from pyOFTools.binning import Directional
from pyOFTools.datasets import InternalDataSet


class DummyGeometry:
    @property
    def positions(self):
        return vectorField([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])

    @property
    def volumes(self):
        return scalarField([0.0, 1.0, 2.0, 3.0])


def create_dataset(field, mask: None, zones: None) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=field,
        geometry=DummyGeometry(),
        mask=mask,
        groups=zones,
    )


def test_directional():
    binning = Directional(
        type="directional", bins=[0.5, 1.5, 2.5], direction=(1, 0, 0), origin=(0, 0, 0)
    )
    dataSet = create_dataset(
        field=scalarField([0.0, 0.0, 0.0, 0.0]),  # are ignored
        mask=None,
        zones=None,
    )
    ds = binning.compute(dataSet)
    assert ds.groups is not None
    assert isinstance(ds.groups, labelList)
    assert np.array_equal(np.asarray(ds.groups), [0, 1, 2, 3])  # 0 and 3 are out of range
