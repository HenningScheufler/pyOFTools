from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any, Optional

import numpy as np
import pandas as pd
import pytest
from pybFoam import boolList, labelList, scalarField, vectorField

from pyOFTools.aggregators import Sum
from pyOFTools.datasets import InternalDataSet
from pyOFTools.tables.csvWriter import CSVWriter
from pyOFTools.workflow import create_workflow

WorkFlow: Any = create_workflow()


@pytest.fixture
def change_test_dir(request: pytest.FixtureRequest) -> Iterator[None]:
    os.chdir(request.fspath.dirname)  # type: ignore[attr-defined]  # fspath is legacy py.path.local API
    yield
    os.chdir(request.config.invocation_dir)  # type: ignore[attr-defined]  # invocation_dir is legacy pytest Config attribute


class DummyGeometry:
    @property
    def positions(self) -> None:
        return None

    @property
    def volumes(self) -> scalarField:
        return scalarField([1.0, 2.0, 3.0])


def create_dataset(
    field: scalarField | vectorField,
    mask: Optional[boolList] = None,
    zones: Optional[labelList] = None,
) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=field,
        geometry=DummyGeometry(),
        mask=mask,
        groups=zones,
    )


@pytest.mark.parametrize(
    "mask,zones,expected",
    [
        (None, None, ([6.0], [6.0, 6.0, 6.0])),
        (boolList([True, False, True]), None, ([4.0], [4.0, 4.0, 4.0])),
        (
            None,
            labelList([1, 2, 2]),
            (
                [[0.0, 0], [1.0, 1], [5.0, 2]],
                [
                    [0.0, 0.0, 0.0, 0],
                    [1.0, 1.0, 1.0, 1],
                    [5.0, 5.0, 5.0, 2],
                ],
            ),
        ),
    ],
)
def test_csv_write_aggregated_dataset(
    change_test_dir: None,
    mask: Optional[boolList],
    zones: Optional[labelList],
    expected: tuple[list[object], list[object]],
) -> None:
    field = scalarField([1.0, 2.0, 3.0])

    workflow = WorkFlow(initial_dataset=create_dataset(field, mask=mask, zones=zones)).then(Sum())
    result = workflow.compute()

    writer = CSVWriter(file_path="test_output.csv")
    writer.create_file()

    assert os.path.isfile("test_output.csv")

    writer.write_result(time=0.0, result=result)

    table = pd.read_csv("test_output.csv")
    if zones:
        assert table.columns.tolist() == ["time", "internal_sum", "group"]
    else:
        assert table.columns.tolist() == ["time", "internal_sum"]

    assert np.allclose(table.iloc[:, 1:], np.array(expected[0]))
    os.remove("test_output.csv")
    assert not os.path.isfile("test_output.csv")

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]),
        mask=mask,
        zones=zones,
    )

    workflow = WorkFlow(initial_dataset=dataSet).then(Sum())
    result = workflow.compute()

    writer = CSVWriter(file_path="test_output.csv")
    writer.create_file()
    assert os.path.isfile("test_output.csv")
    writer.write_result(time=0.0, result=result)

    table = pd.read_csv("test_output.csv")
    if zones:
        assert table.columns.tolist() == [
            "time",
            "internal_sum_0",
            "internal_sum_1",
            "internal_sum_2",
            "group",
        ]
    else:
        assert table.columns.tolist() == [
            "time",
            "internal_sum_0",
            "internal_sum_1",
            "internal_sum_2",
        ]
    assert np.allclose(table.iloc[:, 1:], np.array(expected[1]))
    os.remove("test_output.csv")
    assert not os.path.isfile("test_output.csv")
