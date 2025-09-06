import numpy as np
from pybFoam import scalarField, boolList, labelList
from typing import Literal
import pytest
from pyOFTools.datasets import InternalDataSet, PatchDataSet, SurfaceDataSet, AggregatedDataSet, DataSets
from pyOFTools.node import Node
from pyOFTools.aggregators import Sum, Mean
from pyOFTools.workflow import create_workflow # depends on import order


class DummyMesh:

    @property
    def positions(self):
        return np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])


@Node.register()
class FlipMask(Node):
    type: Literal["flipmask"] = "flipmask"

    def compute(self, dataset: DataSets) -> DataSets:
        dataset.mask = ~np.asarray(dataset.mask)
        return dataset


@Node.register()
class AllTrue(Node):
    type: Literal["alltrue"] = "alltrue"

    def compute(self, dataset: DataSets) -> DataSets:
        dataset.mask[:] = True
        return dataset


WorkFlow = create_workflow()


def test_workflow():
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

    workflow = WorkFlow(initial_dataset=f, steps=[FlipMask()])

    workflow.then(AllTrue())  # chaining example
    assert workflow.initial_dataset == f
    assert isinstance(workflow.steps, list)
    assert len(workflow.steps) == 2
    assert isinstance(workflow.steps[0], FlipMask)
    assert isinstance(workflow.steps[1], AllTrue)

    result = workflow.compute()
    assert (
        workflow.initial_dataset.mask == np.array([True, False, True])
    ).all()  # ensure initial dataset mask unchanged
    assert (
        f.mask == np.array([True, False, True])
    ).all()  # ensure initial dataset mask unchanged
    assert (result.mask == np.array([True, True, True])).all()
    workflow.then(FlipMask())  # chaining example
    result = workflow.compute()
    assert (result.mask == np.array([False, False, False])).all()


def test_aggregation_workflow():
    mask = boolList([True, False, True])
    zones = None
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


    workflow = WorkFlow(initial_dataset=f).then(Sum())  # chaining example

    result = workflow.compute()
    assert isinstance(result, DataSets)
    assert isinstance(result, AggregatedDataSet)
    assert result.name == "internal_sum"
    assert (result.values[0].value == 4.0) # second element is filtered out
