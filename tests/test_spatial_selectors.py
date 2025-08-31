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
        DummyGeometry(positions=vectorField([[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]]))
    )
    mask = box.compute(dataSet)
    assert np.array_equal(mask, [True, False])


def test_sphere_inside():
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    dataSet = create_dataset(
        DummyGeometry(positions=vectorField([[0.5, 0, 0], [2.0, 0, 0]]))
    )
    mask = sphere.compute(dataSet)
    assert np.array_equal(mask, [True, False])


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
    mask = region.compute(dataSet)
    assert np.array_equal(mask, [False, True])


def test_binary_and_region():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.5, 0.5, 0.5), radius=0.2)
    region = BinarySpatialSelector(type="binary", op="and", left=box, right=sphere)
    dataSet = create_dataset(
        DummyGeometry(
            positions=vectorField(
                [
                    [0.5, 0.5, 0.5],  # inside both
                    [1.5, 0.5, 0.5],  # outside box
                    [0.5, 0.5, 0.8],  # inside box but outside sphere
                ]
            )
        )
    )
    mask = region.compute(dataSet)
    assert np.array_equal(mask, [True, False, False])


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


# def test_yaml_round_trip(tmp_path):
#     region = Box(type="box", min=(0, 0, 0), max=(1, 1, 1)) & ~Sphere(
#         type="sphere", center=(0.5, 0.5, 0.5), radius=0.25
#     )
#     coords = np.random.rand(10, 3)
#     mask_before = region.compute(coords)

#     yaml_file = tmp_path / "region.yaml"

#     # Convert the model to a dict with proper serialization for YAML
#     region_dict = region.model_dump(mode="json")

#     with open(yaml_file, "w") as f:
#         yaml.dump(region_dict, f, default_flow_style=False)

#     with open(yaml_file) as f:
#         data = yaml.safe_load(f)

#     # Use Pydantic's discriminated union to deserialize
#     region2 = from_dict(data)
#     mask_after = region2.compute(coords)

#     assert np.array_equal(mask_before, mask_after)
