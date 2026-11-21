"""pyOFTools.parallel must expose the reductions from pybFoam.parallel."""

import pytest

pybfoam_parallel = pytest.importorskip("pybFoam.parallel")


def test_reexports_pybfoam_functions() -> None:
    from pyOFTools import parallel

    for name in ("sum", "min", "max", "weighted_average"):
        assert getattr(parallel, name) is getattr(pybfoam_parallel, name)


def test_mass_weighted_average() -> None:
    from pyOFTools import parallel

    assert parallel.weighted_average([10.0, 20.0], [2.0, 3.0]) == 16.0
