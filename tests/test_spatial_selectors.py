import numpy as np
from pybFoam import scalarField, vectorField, boolList, labelList
import pytest

from pyOFTools.spatial_selectors import (
    Box,
    Sphere,
    NotSpatialSelector,
    BinarySpatialSelector,
    SpatialSelectorModel,
)
from pyOFTools.datasets import InternalDataSet


class DummyGeometry:
    def __init__(self, positions):
        self._positions = positions

    @property
    def positions(self):
        return self._positions

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


def create_dataset(geo) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=scalarField([1.0, 2.0, 3.0]),
        geometry=geo,
        mask=boolList([True, False, True]),
        groups=labelList([1, 2, 1]),
    )


def test_box_inside():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    dataSet = create_dataset(
        DummyGeometry(positions=vectorField([[0.5, 0.5, 0.5],[0.5, 0.5, 0.8] ,[1.5, 1.5, 1.5]]))
    )
    ds = box.compute(dataSet)
    assert np.array_equal(ds.mask, [True, True, False])


def test_sphere_inside():
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    dataSet = create_dataset(
        DummyGeometry(positions=vectorField([[0.5, 0, 0], [2.0, 0, 0]]))
    )
    ds = sphere.compute(dataSet)
    assert np.array_equal(ds.mask, [True, False])


def test_not_region():
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
    assert np.array_equal(ds.mask, [False, True])


def test_binary_and_region():
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
    assert np.array_equal(np.asarray(ds.mask), [True, False, False, False])

def test_binary_or_region():
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
    assert np.array_equal(np.asarray(ds.mask), [True, True, True, False])

def test_operator_overloads_equivalent():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.5, 0.5, 0.5), radius=0.2)

    region_manual = BinarySpatialSelector(
        type="binary", op="and", left=box, right=sphere
    )
    region_op = box & sphere

    # coords = np.array([[0.5, 0.5, 0.5], [2, 2, 2]])
    dataSet = create_dataset(
        DummyGeometry(positions=vectorField([[0.5, 0.5, 0.5], [2, 2, 2]]))
    )
    assert np.array_equal(region_manual.compute(dataSet), region_op.compute(dataSet))

    region_manual = BinarySpatialSelector(
        type="binary", op="or", left=box, right=sphere
    )
    region_op = box | sphere
    assert np.array_equal(region_manual.compute(dataSet), region_op.compute(dataSet))

