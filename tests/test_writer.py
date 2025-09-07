from pybFoam import scalarField, boolList, labelList, vectorField
from pyOFTools.datasets import AggregatedDataSet, AggregatedData, InternalDataSet
import pandas as pd
import numpy as np
from pyOFTools.writer import CSVWriter
import os
import pytest
from pyOFTools.aggregators import Sum
from pyOFTools.workflow import WorkFlow


@pytest.fixture
def change_test_dir(request):
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


class DummyGeometry:
    @property
    def positions(self):
        return None

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


def create_dataset(field, mask=None, zones=None) -> InternalDataSet:
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
def test_csv_write_aggregated_dataset(change_test_dir, mask, zones, expected):
    field = scalarField([1.0, 2.0, 3.0])

    workflow = WorkFlow(
        initial_dataset=create_dataset(field, mask=mask, zones=zones)
    ).then(Sum())  # chaining example
    writer = CSVWriter(file_path="test_output.csv")
    writer.create_file()

    assert os.path.isfile("test_output.csv")

    writer.write_data(time=0.0, workflow=workflow)

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

    workflow = WorkFlow(initial_dataset=dataSet).then(Sum())  # chaining example
    writer = CSVWriter(file_path="test_output.csv")
    writer.create_file()
    assert os.path.isfile("test_output.csv")
    writer.write_data(time=0.0, workflow=workflow)

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
