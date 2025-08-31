import pytest
import numpy as np
from pybFoam import scalarField, vectorField, boolList, labelList, vector
from pyOFTools.aggregators import Sum, Mean  # , Max, Min
from pyOFTools.datasets import InternalDataSet, AggregatedDataSet, AggregatedData


class DummyGeometry:

    @property
    def positions(self):
        return None


def create_dataset(field, mask: None, zones: None) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=field,
        geometry=DummyGeometry(),
        mask=mask,
        groups=zones,
    )


def test_aggregated_data():

    data = AggregatedData(name="data1", value=1.0)
    assert data.name == "data1"
    assert data.value == 1.0


def test_aggregated_dataset():
    dataset = AggregatedDataSet(
        name="test_aggregated",
        values=[
            AggregatedData(name="data1", value=1.0),
            AggregatedData(name="data2", value=2.0),
        ],
    )
    assert dataset.name == "test_aggregated"
    assert dataset.values[0].name == "data1"
    assert dataset.values[0].value == 1.0
    assert dataset.values[1].name == "data2"
    assert dataset.values[1].value == 2.0


@pytest.mark.parametrize(
    "mask,zones,expected",
    [
        (None, None, ([6.0], [6.0, 6.0, 6.0])),
        (boolList([True, False, True]), None, ([4.0], [4.0, 4.0, 4.0])),
        (
            None,
            labelList([1, 2, 2]),
            ([0, 1.0, 5.0], [
                [0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0],
                [5.0, 5.0, 5.0],
            ]),
        ),
    ],
)
def test_sum(mask, zones, expected):

    dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]), mask, zones)
    res = Sum().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "sum"
    res_values = [v.value for v in res.values]
    assert res_values == expected[0]

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]), mask, zones
    )
    res = Sum().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "sum"
    res_values = [v.value for v in res.values]
    if len(res_values) == 1:
        res_values = res_values[0]
    assert res_values == expected[1]


# def test_mean():

#     dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]))
#     res = Mean().compute(dataSet)

#     assert isinstance(res, AggregatedDataSet)
#     assert res.name == "mean"
#     assert res.values[0].name == "internal_mean"
#     assert res.values[0].value == 2.0

#     dataSet = create_dataset(
#         vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])
#     )
#     res = Mean().compute(dataSet)
#     assert isinstance(res, AggregatedDataSet)
#     assert res.name == "mean"
#     assert res.values[0].name == "internal_mean"
#     assert res.values[0].value == [2.0, 2.0, 2.0]


# def test_max():
#     dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]))
#     res = Max().compute(dataSet)
#     assert res == 3.0

#     dataSet = create_dataset(
#         vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]])
#     )
#     res = Max().compute(dataSet)
#     assert res == [3.0, 3.0, 3.0]
