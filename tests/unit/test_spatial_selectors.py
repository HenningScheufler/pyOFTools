import numpy as np
from pybFoam import boolList, labelList, scalarField, vectorField

from pyOFTools.datasets import InternalDataSet
from pyOFTools.spatial_selectors import (
    BinarySpatialSelector,
    Box,
    NotSpatialSelector,
    Sphere,
)


class DummyGeometry:
    def __init__(self, positions: vectorField) -> None:
        self._positions = positions

    @property
    def positions(self) -> vectorField:
        return self._positions

    @property
    def volumes(self) -> scalarField:
        return scalarField([1.0, 2.0, 3.0])


def create_dataset(geo: DummyGeometry) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=scalarField([1.0, 2.0, 3.0]),
        geometry=geo,
        mask=boolList([True, False, True]),
        groups=labelList([1, 2, 1]),
    )


def test_box_inside() -> None:
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    dataSet = create_dataset(
        DummyGeometry(positions=vectorField([[0.5, 0.5, 0.5], [0.5, 0.5, 0.8], [1.5, 1.5, 1.5]]))
    )
    ds = box.compute(dataSet)
    assert isinstance(ds, InternalDataSet)
    assert ds.mask is not None
    assert np.array_equal(np.asarray(ds.mask), [True, True, False])


def test_sphere_inside() -> None:
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    dataSet = create_dataset(DummyGeometry(positions=vectorField([[0.5, 0, 0], [2.0, 0, 0]])))
    ds = sphere.compute(dataSet)
    assert isinstance(ds, InternalDataSet)
    assert ds.mask is not None
    assert np.array_equal(np.asarray(ds.mask), [True, False])


def test_not_region() -> None:
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    region = NotSpatialSelector(type="not", region=sphere)
    dataSet = create_dataset(
        DummyGeometry(
            positions=vectorField(
                [[0.5, 0, 0], [2.0, 0, 0]]  # inside box  # outside box
            )
        )
    )
    ds = region.compute(dataSet)
    assert isinstance(ds, InternalDataSet)
    assert ds.mask is not None
    assert np.array_equal(np.asarray(ds.mask), [False, True])


def test_binary_and_region() -> None:
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.9, 0.9, 0.9), radius=0.3)
    region = BinarySpatialSelector(type="binary", op="and", left=box, right=sphere)
    dataSet = create_dataset(
        DummyGeometry(
            positions=vectorField(
                [
                    [0.9, 0.9, 0.9],  # inside both
                    [1.1, 0.9, 0.9],  # outside box but inside sphere
                    [0.1, 0.1, 0.1],  # inside box but outside sphere
                    [2.0, 2.0, 2.0],  # outside both
                ]
            )
        )
    )
    ds = region.compute(dataSet)
    assert isinstance(ds, InternalDataSet)
    assert np.array_equal(np.asarray(ds.mask), [True, False, False, False])


def test_binary_or_region() -> None:
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.9, 0.9, 0.9), radius=0.3)
    region = BinarySpatialSelector(type="binary", op="or", left=box, right=sphere)
    dataSet = create_dataset(
        DummyGeometry(
            positions=vectorField(
                [
                    [0.9, 0.9, 0.9],  # inside both
                    [1.1, 0.9, 0.9],  # outside box but inside sphere
                    [0.1, 0.1, 0.1],  # inside box but outside sphere
                    [2.0, 2.0, 2.0],  # outside both
                ]
            )
        )
    )
    ds = region.compute(dataSet)
    assert isinstance(ds, InternalDataSet)
    assert np.array_equal(np.asarray(ds.mask), [True, True, True, False])


def test_operator_overloads_equivalent() -> None:
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.5, 0.5, 0.5), radius=0.2)

    region_manual = BinarySpatialSelector(type="binary", op="and", left=box, right=sphere)
    region_op = box & sphere

    # coords = np.array([[0.5, 0.5, 0.5], [2, 2, 2]])
    dataSet = create_dataset(DummyGeometry(positions=vectorField([[0.5, 0.5, 0.5], [2, 2, 2]])))
    ds_manual = region_manual.compute(dataSet)
    ds_op = region_op.compute(dataSet)
    assert isinstance(ds_manual, InternalDataSet)
    assert isinstance(ds_op, InternalDataSet)
    assert np.array_equal(np.asarray(ds_manual.mask), np.asarray(ds_op.mask))

    region_manual = BinarySpatialSelector(type="binary", op="or", left=box, right=sphere)
    region_op = box | sphere
    ds_manual2 = region_manual.compute(dataSet)
    ds_op2 = region_op.compute(dataSet)
    assert isinstance(ds_manual2, InternalDataSet)
    assert isinstance(ds_op2, InternalDataSet)
    assert np.array_equal(np.asarray(ds_manual2.mask), np.asarray(ds_op2.mask))
