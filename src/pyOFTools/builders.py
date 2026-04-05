"""
Builders for simplified post-processing workflows.

This module provides high-level functions for creating workflows from
OpenFOAM fields, surfaces, and lines.

Geometry builders:
    - ``field(mesh, name)`` --- volume field
    - ``iso_surface(mesh, iso_field, iso_value)`` --- iso-surface (geometry only)
    - ``plane(mesh, point, normal)`` --- cutting plane (geometry only)
    - ``line(mesh, name, start, end, n, field_name)`` --- line sample

Field selection nodes (used with ``|``):
    - ``area()`` --- face area magnitudes from surface geometry
    - ``sample(mesh, field_name)`` --- interpolate a volume field onto a surface

Example::

    iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()
    iso_surface(mesh, "alpha.water", 0.5) | sample(mesh, "p") | Mean()
    plane(mesh, point=(0.5,0,0), normal=(1,0,0)) | sample(mesh, "T") | Max()
    field(mesh, "p") | VolIntegrate()
    line(mesh, "centreline", (0,0,0), (1,0,0), 100, "p") | Mean()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Literal, Tuple, Union

from pybFoam import volScalarField
from pydantic import BaseModel

# Import aggregators to populate Node registry
from . import aggregators  # noqa: F401
from .datasets import InternalDataSet, SurfaceDataSet
from .geometry import FvMeshInternalAdapter
from .interpolation import SurfaceInterpolator
from .node import Node
from .residuals import residual_dataset
from .surfaces import create_iso_surface, create_plane

if TYPE_CHECKING:
    from pybFoam import fvMesh

    from .datasets import DataSets


__all__ = [
    "area",
    "field",
    "iso_surface",
    "line",
    "plane",
    "residuals",
    "sample",
]


# ---------------------------------------------------------------------------
# Pipe nodes: area() and sample()
# ---------------------------------------------------------------------------


@Node.register()
class Area(BaseModel):
    """Node that populates a SurfaceDataSet field with face area magnitudes."""

    type: Literal["area"] = "area"

    def compute(self, dataset: DataSets) -> DataSets:  # type: ignore[override]
        if not isinstance(dataset, SurfaceDataSet):
            raise TypeError(f"area() requires a SurfaceDataSet, got {type(dataset).__name__}")
        dataset.field = dataset.geometry.face_area_magnitudes
        return dataset


@Node.register()
class Sample(BaseModel):
    """Node that interpolates a volume field onto a surface."""

    type: Literal["sample"] = "sample"
    mesh: Any  # fvMesh
    field_name: str
    scheme: str = "cellPoint"
    model_config = {"arbitrary_types_allowed": True}

    def compute(self, dataset: DataSets) -> DataSets:  # type: ignore[override]
        if not isinstance(dataset, SurfaceDataSet):
            raise TypeError(f"sample() requires a SurfaceDataSet, got {type(dataset).__name__}")
        vf = volScalarField.from_registry(self.mesh, self.field_name)
        interp = SurfaceInterpolator(scheme=self.scheme)
        dataset.field = interp.interpolate(vf, dataset.geometry._surface)
        return dataset


def area() -> Area:
    """Face area magnitudes from surface geometry.

    Use in a pipe after a surface builder::

        iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()
    """
    return Area()


def sample(mesh: fvMesh, field_name: str, scheme: str = "cellPoint") -> Sample:
    """Interpolate a volume field onto a surface.

    Use in a pipe after a surface builder::

        iso_surface(mesh, "alpha.water", 0.5) | sample(mesh, "p") | Mean()

    Args:
        mesh: OpenFOAM mesh object
        field_name: Name of the volume field to sample
        scheme: Interpolation scheme (default: "cellPoint")
    """
    return Sample(mesh=mesh, field_name=field_name, scheme=scheme)


# ---------------------------------------------------------------------------
# Geometry builders
# ---------------------------------------------------------------------------


def field(mesh: fvMesh, name: str) -> Any:  # WorkFlow
    """Create a WorkFlow from a registered volScalarField.

    Args:
        mesh: OpenFOAM mesh object
        name: Name of the field in the object registry

    Example::

        field(mesh, "alpha.water") | VolIntegrate()
    """
    from .workflow import WorkFlow

    vf = volScalarField.from_registry(mesh, name)
    return WorkFlow(  # type: ignore[misc]
        initial_dataset=InternalDataSet(
            name=name,
            field=vf["internalField"],
            geometry=FvMeshInternalAdapter(mesh),
        )
    )


def iso_surface(mesh: fvMesh, iso_field: str, iso_value: float) -> Any:  # WorkFlow
    """Create a WorkFlow for an iso-surface (geometry only, no field).

    Pipe into ``area()`` or ``sample()`` to select what to compute::

        iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()
        iso_surface(mesh, "alpha.water", 0.5) | sample(mesh, "p") | Mean()

    Args:
        mesh: OpenFOAM mesh object
        iso_field: Name of the scalar field to create iso-surface from
        iso_value: Value for the iso-surface
    """
    from .workflow import WorkFlow

    surface = create_iso_surface(
        name=f"iso_{iso_field}",
        mesh=mesh,
        field=None,
        iso_field_name=iso_field,
        iso_value=iso_value,
    )
    return WorkFlow(initial_dataset=surface)  # type: ignore[misc]


def plane(
    mesh: fvMesh,
    point: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    normal: Tuple[float, float, float] = (1.0, 0.0, 0.0),
) -> Any:  # WorkFlow
    """Create a WorkFlow for a cutting plane (geometry only, no field).

    Pipe into ``area()`` or ``sample()`` to select what to compute::

        plane(mesh, point=(0.5,0,0), normal=(1,0,0)) | sample(mesh, "T") | Max()

    Args:
        mesh: OpenFOAM mesh object
        point: Point on the plane (x, y, z)
        normal: Normal vector (nx, ny, nz)
    """
    from .workflow import WorkFlow

    surface = create_plane(
        name="plane",
        mesh=mesh,
        field=None,
        point=point,
        normal=normal,
    )
    return WorkFlow(initial_dataset=surface)  # type: ignore[misc]


def line(
    mesh: fvMesh,
    name: str,
    start: Union[Tuple[float, float, float], List[float]],
    end: Union[Tuple[float, float, float], List[float]],
    n_points: int,
    field_name: str,
    scheme: str = "cellPoint",
) -> Any:  # WorkFlow
    """Create a WorkFlow from a uniform line sample.

    Args:
        mesh: OpenFOAM mesh object
        name: Name for the sampled set
        start: Start point (x, y, z)
        end: End point (x, y, z)
        n_points: Number of sample points
        field_name: Name of the volume field to sample
        scheme: Interpolation scheme (default: "cellPoint")

    Example::

        line(mesh, "centreline", (0,0,0), (1,0,0), 100, "p") | Mean()
    """
    from .sets import create_uniform_set
    from .workflow import WorkFlow

    vf = volScalarField.read_field(mesh, field_name)
    dataset = create_uniform_set(
        mesh=mesh,
        name=name,
        start=start,
        end=end,
        n_points=n_points,
        field=vf,
        scheme=scheme,
    )
    return WorkFlow(initial_dataset=dataset)  # type: ignore[misc]


def residuals(mesh: fvMesh) -> Any:  # WorkFlow
    """Create a WorkFlow for solver residuals.

    Args:
        mesh: OpenFOAM mesh object

    Example::

        residuals(mesh)
    """
    from .workflow import WorkFlow

    return WorkFlow(initial_dataset=residual_dataset(mesh))  # type: ignore[misc]
