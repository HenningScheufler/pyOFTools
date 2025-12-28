from typing import Protocol, runtime_checkable

from pybFoam import fvMesh, scalarField, vectorField


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
    def __init__(self, mesh: "fvMesh") -> None:
        self._mesh = mesh

    @property
    def positions(self) -> vectorField:
        return self._mesh.C()["internalField"]

    @property
    def volumes(self) -> scalarField:
        return self._mesh.V()
