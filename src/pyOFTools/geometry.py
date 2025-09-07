from pybFoam import vectorField, scalarField
from typing import Protocol, runtime_checkable


@runtime_checkable
class InternalMesh(Protocol):
    @property
    def positions(self) -> vectorField: ...

    @property
    def volumes(self) -> scalarField: ...


@runtime_checkable
class BoundaryMesh(Protocol):
    @property
    def positions(self) -> vectorField: ...


@runtime_checkable
class SurfaceMesh(Protocol):
    @property
    def positions(self) -> vectorField: ...


class FvMeshInternalAdapter:
    def __init__(self, mesh):
        self._mesh = mesh

    @property
    def positions(self):
        return self._mesh.C()["internalField"]

    @property
    def volumes(self):
        return self._mesh.V()
