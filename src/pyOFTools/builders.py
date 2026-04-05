"""
Builders for simplified post-processing workflows.

This module provides high-level functions for creating workflows from OpenFOAM fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple, Union

from pybFoam import scalarField, volScalarField

# Import aggregators to populate Node registry
from . import aggregators  # noqa: F401
from .datasets import InternalDataSet
from .geometry import FvMeshInternalAdapter
from .residuals import residual_dataset
from .surfaces import create_iso_surface

if TYPE_CHECKING:
    from pybFoam import fvMesh


__all__ = [
    "field",
    "iso_surface",
    "line",
    "residuals",
]


def field(mesh: fvMesh, name: str) -> Any:  # WorkFlow
    """
    Create a WorkFlow from a registered volScalarField.

    This is a convenience function that wraps field registry lookup,
    internal field extraction, and geometry adaptation into a single call.

    Args:
        mesh: OpenFOAM mesh object
        name: Name of the field in the object registry

    Returns:
        WorkFlow with InternalDataSet initialized

    Example:
        >>> from pyOFTools.builders import field
        >>> from pyOFTools.aggregators import VolIntegrate
        >>>
        >>> workflow = field(mesh, "alpha.water") | VolIntegrate()
        >>> result = workflow.compute()
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
    """
    Create a WorkFlow for iso-surface with face area magnitudes.

    This creates an iso-surface from a field and sets up the workflow
    with face area magnitudes as the field values, useful for area calculations.

    Args:
        mesh: OpenFOAM mesh object
        iso_field: Name of the field to create iso-surface from
        iso_value: Value for the iso-surface

    Returns:
        WorkFlow with SurfaceDataSet initialized

    Example:
        >>> from pyOFTools.builders import iso_surface
        >>> from pyOFTools.aggregators import Sum
        >>>
        >>> # Calculate free surface area at alpha.water = 0.5
        >>> workflow = iso_surface(mesh, "alpha.water", 0.5) | Sum()
        >>> area = workflow.compute()
    """
    from .workflow import WorkFlow

    surface = create_iso_surface(
        name=f"iso_{iso_field}",
        mesh=mesh,
        field=scalarField([0.0]),  # Dummy field, replaced below
        iso_field_name=iso_field,
        iso_value=iso_value,
    )
    surface.field = surface.geometry.face_area_magnitudes
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
    """
    Create a WorkFlow from a uniform line sample.

    Reads the field, creates a uniform set, interpolates, and returns
    a WorkFlow ready for aggregation.

    Args:
        mesh: OpenFOAM mesh object
        name: Name for the sampled set
        start: Start point (x, y, z)
        end: End point (x, y, z)
        n_points: Number of sample points
        field_name: Name of the volume field to sample
        scheme: Interpolation scheme (default: "cellPoint")

    Returns:
        WorkFlow with PointDataSet initialized

    Example:
        >>> from pyOFTools.builders import line
        >>> from pyOFTools.aggregators import Mean
        >>>
        >>> workflow = line(mesh, "centreline", (0,0,0), (1,0,0), 100, "p") | Mean()
        >>> result = workflow.compute()
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
    """
    Create a WorkFlow for solver residuals.

    This creates a workflow that extracts solver performance data
    (residuals) from the mesh's solver performance dictionary.

    Args:
        mesh: OpenFOAM mesh object

    Returns:
        WorkFlow with residual dataset initialized

    Example:
        >>> from pyOFTools.builders import residuals
        >>>
        >>> # Get solver residuals
        >>> workflow = residuals(mesh)
        >>> data = workflow.compute()
    """
    from .workflow import WorkFlow

    return WorkFlow(initial_dataset=residual_dataset(mesh))  # type: ignore[misc]
