from typing import Literal, cast

import numpy as np
from pybFoam import boolList, labelList, scalarField, vectorField

from pyOFTools.aggregators import Sum
from pyOFTools.datasets import (
    AggregatedDataSet,
    DataSets,
    FieldDataSets,
    InternalDataSet,
)
from pyOFTools.node import Node
from pyOFTools.workflow import create_workflow  # depends on import order


class DummyMesh:
    @property
    def positions(self) -> vectorField:
        return vectorField([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    @property
    def volumes(self) -> scalarField:
        return scalarField([1.0, 2.0, 3.0])


@Node.register()
class FlipMask(Node):
    type: Literal["flipmask"] = "flipmask"

    def compute(self, dataset: DataSets) -> DataSets:
        field_dataset = cast(FieldDataSets, dataset)
        field_dataset.mask = ~np.asarray(field_dataset.mask)  # type: ignore[assignment]  # ndarray accepted by pydantic boolList validator
        return field_dataset


@Node.register()
class AllTrue(Node):
    type: Literal["alltrue"] = "alltrue"

    def compute(self, dataset: DataSets) -> DataSets:
        field_dataset = cast(FieldDataSets, dataset)
        assert field_dataset.mask is not None
        field_dataset.mask[:] = True  # type: ignore[index]
        return field_dataset


WorkFlow = create_workflow()


def test_workflow() -> None:
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
        np.asarray(workflow.initial_dataset.mask) == np.array([True, False, True])
    ).all()  # ensure initial dataset mask unchanged
    assert (
        np.asarray(f.mask) == np.array([True, False, True])
    ).all()  # ensure initial dataset mask unchanged
    assert (np.asarray(result.mask) == np.array([True, True, True])).all()
    workflow.then(FlipMask())  # chaining example
    result = workflow.compute()
    assert (np.asarray(result.mask) == np.array([False, False, False])).all()


def test_aggregation_workflow() -> None:
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
    assert isinstance(result, AggregatedDataSet)
    assert result.name == "internal_sum"
    assert result.values[0].value == 4.0  # second element is filtered out
