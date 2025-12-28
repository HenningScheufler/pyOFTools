import numpy as np
from pybFoam import scalarField, boolList, labelList, vectorField
import pytest
from pyOFTools.datasets import InternalDataSet, PatchDataSet, SurfaceDataSet, PointDataSet


class DummyInternalMesh:
    """Implements InternalMesh protocol."""
    @property
    def positions(self):
        return vectorField([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    @property
    def volumes(self):
        return scalarField([1.0, 2.0, 3.0])


class DummyBoundaryMesh:
    """Implements BoundaryMesh protocol."""
    @property
    def positions(self):
        return vectorField([[0, 0, 0], [1, 1, 1]])


class DummySurfaceMesh:
    """Implements SurfaceMesh protocol."""
    @property
    def positions(self):
        return vectorField([[0, 0, 0], [1, 1, 1], [2, 2, 2]])

    @property
    def face_areas(self):
        return vectorField([[0, 0, 1.0], [0, 0, 2.0], [0, 0, 3.0]])

    @property
    def face_area_magnitudes(self):
        return scalarField([1.0, 2.0, 3.0])

    @property
    def total_area(self):
        return 6.0


class DummyPointMesh:
    """Implements PointMesh protocol."""
    @property
    def positions(self):
        return vectorField([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
    
    @property
    def distance(self) -> scalarField:
        """Cumulative distance along the set (or arbitrary metric for clouds)."""
        return scalarField([0.0, 1.732, 3.464])


def test_internal_field_creation():
    mask = boolList([True, False, True])
    zones = labelList([1, 2, 1])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummyInternalMesh()
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
    assert isinstance(f.geometry, DummyInternalMesh)


def test_patch_field_creation():
    mask = boolList([False, True])
    zones = labelList([0, 1])
    field = scalarField([1.0, 2.0])
    geometry = DummyBoundaryMesh()
    f = PatchDataSet(
        name="patch",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "patch"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummyBoundaryMesh)


def test_surface_field_creation():
    mask = boolList([True, True, False])
    zones = labelList([2, 2, 3])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummySurfaceMesh()
    f = SurfaceDataSet(
        name="surface",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "surface"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummySurfaceMesh)


def test_point_field_creation():
    mask = boolList([True, False, True])
    zones = labelList([1, 2, 1])
    field = scalarField([1.0, 2.0, 3.0])
    geometry = DummyPointMesh()
    f = PointDataSet(
        name="point",
        field=field,
        geometry=geometry,
        mask=mask,
        groups=zones,
    )
    assert f.name == "point"
    assert (np.asarray(f.mask) == mask).all()
    assert (np.asarray(f.groups) == zones).all()
    assert f.field == field
    assert isinstance(f.geometry, DummyPointMesh)
