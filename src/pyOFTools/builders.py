"""
Builders for simplified post-processing workflows.

This module provides high-level functions for creating workflows from OpenFOAM fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pybFoam import scalarField, volScalarField

# Import aggregators to populate Node registry
from . import aggregators  # noqa: F401
from .datasets import InternalDataSet
from .geometry import FvMeshInternalAdapter
from .residuals import residual_dataset
from .surfaces import create_iso_surface

if TYPE_CHECKING:
    from pybFoam import fvMesh

    from .workflow import WorkFlow

__all__ = [
    "field",
    "iso_surface",
    "residuals",
]


def field(mesh: fvMesh, name: str) -> WorkFlow:
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
    return WorkFlow(
        initial_dataset=InternalDataSet(
            name=name,
            field=vf["internalField"],
            geometry=FvMeshInternalAdapter(mesh),
        )
    )


def iso_surface(mesh: fvMesh, iso_field: str, iso_value: float) -> WorkFlow:
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
    return WorkFlow(initial_dataset=surface)


def residuals(mesh: fvMesh) -> WorkFlow:
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

    return WorkFlow(initial_dataset=residual_dataset(mesh))
