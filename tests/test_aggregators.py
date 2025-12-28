import pytest
from pybFoam import boolList, labelList, scalarField, vector, vectorField

from pyOFTools.aggregators import Max, Min, Sum, VolIntegrate
from pyOFTools.datasets import AggregatedData, AggregatedDataSet, InternalDataSet


class DummyGeometry:
    @property
    def positions(self):
        return None

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


def create_dataset(field, mask: None, zones: None) -> InternalDataSet:
    return InternalDataSet(
        name="internal",
        field=field,
        geometry=DummyGeometry(),
        mask=mask,
        groups=zones,
    )


def test_aggregated_data():
    data = AggregatedData(value=1.0, group=[0, 0], group_name=["A", "B"])
    assert data.value == 1.0
    assert data.group == [0, 0]
    assert data.group_name == ["A", "B"]

    data = AggregatedData(value=1.0)
    assert data.value == 1.0
    assert data.group is None
    assert data.group_name is None


def test_aggregated_dataset():
    dataset = AggregatedDataSet(
        name="test_aggregated",
        values=[
            AggregatedData(value=1.0, group=[0, 0], group_name=["A", "B"]),
            AggregatedData(value=2.0, group=[1, 1], group_name=["A", "B"]),
        ],
    )
    assert dataset.name == "test_aggregated"
    assert dataset.values[0].value == 1.0
    assert dataset.values[1].value == 2.0
    assert dataset.headers == ["test_aggregated", "A", "B"]
    assert dataset.grouped_values == [[1.0, 0, 0], [2.0, 1, 1]]

    dataset = AggregatedDataSet(
        name="test_aggregated",
        values=[
            AggregatedData(value=vector(1.0, 1.0, 1.0), group=[0], group_name=["A"]),
            AggregatedData(value=vector(2.0, 2.0, 2.0), group=[1], group_name=["A"]),
        ],
    )
    assert dataset.name == "test_aggregated"
    assert dataset.values[0].value == vector(1.0, 1.0, 1.0)
    assert dataset.values[1].value == vector(2.0, 2.0, 2.0)
    assert dataset.headers == [
        "test_aggregated_0",
        "test_aggregated_1",
        "test_aggregated_2",
        "A",
    ]
    assert dataset.grouped_values == [[1.0, 1.0, 1.0, 0], [2.0, 2.0, 2.0, 1]]


@pytest.mark.parametrize(
    "mask,zones,expected",
    [
        (None, None, ([6.0], [6.0, 6.0, 6.0])),
        (boolList([True, False, True]), None, ([4.0], [4.0, 4.0, 4.0])),
        (
            None,
            labelList([1, 2, 2]),
            (
                [0, 1.0, 5.0],
                [
                    [0.0, 0.0, 0.0],
                    [1.0, 1.0, 1.0],
                    [5.0, 5.0, 5.0],
                ],
            ),
        ),
    ],
)
def test_sum(mask, zones, expected):
    dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]), mask, zones)
    res = Sum().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_sum"
    res_values = [v.value for v in res.values]
    assert res_values == expected[0]

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]), mask, zones
    )
    res = Sum().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_sum"
    res_values = [v.value for v in res.values]
    if len(res_values) == 1:
        res_values = res_values[0]
    assert res_values == expected[1]


def test_volIntegrate():
    dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]), None, None)
    res = VolIntegrate().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_volIntegrate"
    res_values = [v.value for v in res.values]
    assert res_values == [1.0 + 2.0 * 2 + 3.0 * 3]  # 1*1 + 2*2 + 3*3 = 14.0

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]), None, None
    )
    res = VolIntegrate().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_volIntegrate"
    res_values = [v.value for v in res.values]
    if len(res_values) == 1:
        res_values = res_values[0]
    assert res_values == [14.0, 14.0, 14.0]


@pytest.mark.parametrize(
    "mask,zones,expected",
    [
        (None, None, ([3.0], [3.0, 3.0, 3.0])),
        (boolList([True, False, True]), None, ([3.0], [3.0, 3.0, 3.0])),
        (
            None,
            labelList([1, 2, 2]),
            (
                [-1000000000000000.0, 1.0, 3.0],
                [
                    [-1000000000000000.0, -1000000000000000.0, -1000000000000000.0],
                    [1.0, 1.0, 1.0],
                    [3.0, 3.0, 3.0],
                ],
            ),
        ),
    ],
)
def test_max(mask, zones, expected):
    dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]), mask, zones)
    res = Max().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_max"
    res_values = [v.value for v in res.values]
    assert res_values == expected[0]

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]), mask, zones
    )
    res = Max().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_max"
    res_values = [v.value for v in res.values]
    if len(res_values) == 1:
        res_values = res_values[0]
    assert res_values == expected[1]


@pytest.mark.parametrize(
    "mask,zones,expected",
    [
        (None, None, ([1.0], [1.0, 1.0, 1.0])),
        (boolList([True, False, True]), None, ([1.0], [1.0, 1.0, 1.0])),
        (
            None,
            labelList([1, 2, 2]),
            (
                [1000000000000000.0, 1.0, 2.0],
                [
                    [1000000000000000.0, 1000000000000000.0, 1000000000000000.0],
                    [1.0, 1.0, 1.0],
                    [2.0, 2.0, 2.0],
                ],
            ),
        ),
    ],
)
def test_min(mask, zones, expected):
    dataSet = create_dataset(scalarField([1.0, 2.0, 3.0]), mask, zones)
    res = Min().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_min"
    res_values = [v.value for v in res.values]
    assert res_values == expected[0]

    dataSet = create_dataset(
        vectorField([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]), mask, zones
    )
    res = Min().compute(dataSet)
    assert isinstance(res, AggregatedDataSet)
    assert res.name == "internal_min"
    res_values = [v.value for v in res.values]
    if len(res_values) == 1:
        res_values = res_values[0]
    assert res_values == expected[1]
