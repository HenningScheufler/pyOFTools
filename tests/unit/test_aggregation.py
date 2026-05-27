from pybFoam import boolList, labelList, mag, scalarField, vector, vectorField

from pyOFTools import aggregation


def test_mag() -> None:
    s = -10
    assert mag(s) == 10


def test_sum() -> None:
    field = scalarField([1, 2, 3])
    assert aggregation.sum(field, boolList([True, True, True]), None).values[0] == 6
    assert aggregation.sum(field, boolList([True, True, True]), None).group is None
    assert aggregation.sum(field, None, None).values[0] == 6
    assert aggregation.sum(field, boolList([True, False, True]), None).values[0] == 4

    field_v = vectorField([vector(1, 2, 3), vector(4, 5, 6)])
    assert aggregation.sum(field_v, None, None).values[0] == vector(5, 7, 9)
    assert aggregation.sum(field_v, boolList([True, True]), None).values[0] == vector(5, 7, 9)
    assert aggregation.sum(field_v, boolList([True, False]), None).values[0] == vector(1, 2, 3)

    # # with groupby
    field = scalarField([1, 2, 3])

    agg_res = aggregation.sum(field, None, labelList([0, 1, 1]))
    assert agg_res.values[0] == 1
    assert agg_res.values[1] == 5
    assert agg_res.group is not None
    assert agg_res.group[0] == 0
    assert agg_res.group[1] == 1

    agg_res = aggregation.sum(field, boolList([True, False, True]), labelList([0, 1, 1]))
    assert agg_res.values[0] == 1
    assert agg_res.values[1] == 3
    assert agg_res.group is not None
    assert agg_res.group[0] == 0
    assert agg_res.group[1] == 1

    # with scaling factor
    field = scalarField([1, 2, 3])
    scalingFactor = scalarField([2, 4, 4])
    agg_res = aggregation.sum(field, None, labelList([0, 1, 1]), scalingFactor=scalingFactor)
    assert agg_res.values[0] == 2
    assert agg_res.values[1] == 20
    assert agg_res.group is not None
    assert agg_res.group[0] == 0
    assert agg_res.group[1] == 1


def test_mean() -> None:
    field = scalarField([1, 2, 3])
    assert aggregation.mean(field, None, None).values[0] == 2
    assert aggregation.mean(field, None, None).group is None
    assert aggregation.mean(field, boolList([True, True, True]), None).values[0] == 2
    assert aggregation.mean(field, boolList([True, False, True]), None).values[0] == 2

    field_v = vectorField([vector(1, 2, 3), vector(4, 5, 6)])
    assert aggregation.mean(field_v, None, None).values[0] == vector(2.5, 3.5, 4.5)
    assert aggregation.mean(field_v, boolList([True, True]), None).values[0] == vector(
        2.5, 3.5, 4.5
    )
    assert aggregation.mean(field_v, boolList([True, False]), None).values[0] == vector(1, 2, 3)

    # # with groupby
    field = scalarField([1, 2, 3])
    assert aggregation.mean(field, None, labelList([0, 1, 1])).values[0] == 1
    assert aggregation.mean(field, None, labelList([0, 1, 1])).values[1] == 2.5
    grp = aggregation.mean(field, None, labelList([0, 1, 1])).group
    assert grp is not None
    assert grp[0] == 0
    assert grp[1] == 1

    assert (
        aggregation.mean(field, boolList([True, False, True]), labelList([0, 1, 1])).values[0] == 1
    )
    assert (
        aggregation.mean(field, boolList([True, False, True]), labelList([0, 1, 1])).values[1] == 3
    )

    # with scaling factor
    field = scalarField([1, 28, 3])
    scalingFactor = scalarField([2, 6, 4])
    agg_res = aggregation.mean(field, None, labelList([0, 1, 1]), scalingFactor=scalingFactor)
    assert agg_res.values[0] == 1
    assert agg_res.values[1] == 18.0
    assert agg_res.group is not None
    assert agg_res.group[0] == 0
    assert agg_res.group[1] == 1

    # with scaling factor empty groups
    field = scalarField([1, 28, 3])
    scalingFactor = scalarField([2, 6, 4])
    agg_res = aggregation.mean(field, None, labelList([1, 2, 2]), scalingFactor=scalingFactor)
    assert agg_res.values[0] == 1000000000000000.0  # empty group
    assert agg_res.values[1] == 1.0
    assert agg_res.values[2] == 18.0
    assert agg_res.group is not None
    assert agg_res.group[0] == 0
    assert agg_res.group[1] == 1
    assert agg_res.group[2] == 2


def test_min() -> None:
    field = scalarField([1, 2, 3])
    assert aggregation.min(field, None, None).values[0] == 1
    assert aggregation.min(field, None, None).group is None
    assert aggregation.min(field, boolList([True, True, True]), None).values[0] == 1
    assert aggregation.min(field, boolList([True, False, True]), None).values[0] == 1

    field_v = vectorField([vector(1, 2, 3), vector(4, 5, 6)])
    assert aggregation.min(field_v, None, None).values[0] == vector(1, 2, 3)
    assert aggregation.min(field_v, boolList([True, True]), None).values[0] == vector(1, 2, 3)
    assert aggregation.min(field_v, boolList([True, False]), None).values[0] == vector(1, 2, 3)

    # # with groupby
    field = scalarField([1, 2, 3])
    assert aggregation.min(field, None, labelList([0, 1, 1])).values[0] == 1
    assert aggregation.min(field, None, labelList([0, 1, 1])).values[1] == 2
    grp = aggregation.min(field, None, labelList([0, 1, 1])).group
    assert grp is not None
    assert grp[0] == 0
    assert grp[1] == 1

    assert (
        aggregation.min(field, boolList([True, False, True]), labelList([0, 1, 1])).values[0] == 1
    )
    assert (
        aggregation.min(field, boolList([True, False, True]), labelList([0, 1, 1])).values[1] == 3
    )


def test_max() -> None:
    field = scalarField([1, 2, 3])
    assert aggregation.max(field, None, None).values[0] == 3
    assert aggregation.max(field, None, None).group is None
    assert aggregation.max(field, boolList([True, True, True]), None).values[0] == 3
    assert aggregation.max(field, boolList([True, False, True]), None).values[0] == 3

    field_v = vectorField([vector(1, 2, 3), vector(4, 5, 6)])
    assert aggregation.max(field_v, None, None).values[0] == vector(4, 5, 6)
    assert aggregation.max(field_v, boolList([True, True]), None).values[0] == vector(4, 5, 6)
    assert aggregation.max(field_v, boolList([True, False]), None).values[0] == vector(1, 2, 3)

    # # with groupby
    field = scalarField([1, 2, 3])
    assert aggregation.max(field, None, labelList([0, 1, 1])).values[0] == 1
    assert aggregation.max(field, None, labelList([0, 1, 1])).values[1] == 3
    grp = aggregation.max(field, None, labelList([0, 1, 1])).group
    assert grp is not None
    assert grp[0] == 0
    assert grp[1] == 1

    assert (
        aggregation.max(field, boolList([True, False, True]), labelList([0, 1, 1])).values[0] == 1
    )
    assert (
        aggregation.max(field, boolList([True, False, True]), labelList([0, 1, 1])).values[1] == 3
    )
