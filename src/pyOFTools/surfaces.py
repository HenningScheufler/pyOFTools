"""
Convenience utilities for creating common surface types.

This module provides factory functions for easily creating different types
of sampled surfaces without dealing with OpenFOAM dictionary setup directly.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

from pybFoam import Word, boolList, dictionary, fvMesh, labelList, vector, wordList
from pybFoam.sampling import sampledSurface
from pybFoam.sampling.surface_configs import (
    SampledIsoSurfaceConfig,
    SampledPlaneConfig,
)

from .datasets import FieldType, SurfaceDataSet
from .geometry import SampledSurfaceAdapter


def _to_tuple(
    point: Union[Tuple[float, float, float], Dict[str, float]],
) -> Tuple[float, float, float]:
    """Convert point from dict or tuple to tuple."""
    if isinstance(point, dict):
        return (point.get("x", 0.0), point.get("y", 0.0), point.get("z", 0.0))
    return point


def create_plane(
    name: str,
    mesh: fvMesh,
    field: FieldType,
    point: Tuple[float, float, float],
    normal: Tuple[float, float, float],
    triangulate: bool = False,
    mask: Optional[boolList] = None,
    groups: Optional[labelList] = None,
) -> SurfaceDataSet:
    config = SampledPlaneConfig(point=list(point), normal=list(normal), triangulate=triangulate)

    plane_dict = config.to_foam_dict()

    surface = sampledSurface.New(Word(name), mesh, plane_dict)
    surface.update()

    surfData = SurfaceDataSet(name=name, field=field, geometry=SampledSurfaceAdapter(surface))

    return surfData


def create_patch_surface(
    mesh: fvMesh, name: str, patches: List[str], triangulate: bool = False
) -> sampledSurface:
    """
    Create a surface from one or more mesh boundary patches.

    This is useful for sampling fields on boundary surfaces, such as walls,
    inlets, or outlets.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the surface
        patches: List of patch names to include in the surface
        triangulate: Whether to triangulate the surface (default: False)

    Returns:
        sampledPatch surface instance

    Example:
        >>> from pyOFTools.surfaces import create_patch_surface
        >>>
        >>> # Sample on all wall boundaries
        >>> wall_surface = create_patch_surface(
        ...     mesh,
        ...     "walls",
        ...     patches=["leftWall", "rightWall", "bottomWall"]
        ... )
    """

    patch_dict = dictionary()
    patch_dict.set("type", Word("patch"))
    patch_dict.set("patches", wordList(patches))  # wordList expects list of strings
    if triangulate:
        patch_dict.set("triangulate", True)

    surface = sampledSurface.New(Word(name), mesh, patch_dict)
    surface.update()
    return surface


def create_cutting_plane(
    mesh: fvMesh,
    name: str,
    point: Tuple[float, float, float],
    normal: Tuple[float, float, float],
    interpolate: bool = True,
) -> sampledSurface:
    """
    Create a cutting plane surface using the cuttingPlane algorithm.

    Similar to sampledPlane but uses a different algorithm that may produce
    better results in some cases.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the surface
        point: Point on the plane (x, y, z)
        normal: Normal vector (nx, ny, nz)
        interpolate: Whether to interpolate values (default: True)

    Returns:
        sampledCuttingPlane surface instance

    Example:
        >>> from pyOFTools.surfaces import create_cutting_plane
        >>>
        >>> # Create a horizontal plane at z=0.1
        >>> surface = create_cutting_plane(
        ...     mesh,
        ...     "horizontal",
        ...     point=(0, 0, 0.1),
        ...     normal=(0, 0, 1)
        ... )
    """

    # Convert dict to tuple if needed
    point = _to_tuple(point)
    normal = _to_tuple(normal)

    plane_dict = dictionary()
    plane_dict.set("type", Word("cuttingPlane"))
    plane_dict.set("point", vector(*point))
    plane_dict.set("normal", vector(*normal))
    if not interpolate:
        plane_dict.set("interpolate", False)

    surface = sampledSurface.New(Word(name), mesh, plane_dict)
    surface.update()
    return surface


def create_iso_surface(
    name: str, mesh: fvMesh, field: FieldType, iso_field_name: str, iso_value: float
) -> SurfaceDataSet:
    """
    Create an iso-surface of a scalar field.

    An iso-surface is the 3D equivalent of a contour line, representing
    all points where a field has a specific value.

    Args:
        name: Name for the surface
        mesh: OpenFOAM mesh
        field: Field to sample on the surface
        iso_field_name: Name of the scalar field to create iso-surface from
        iso_value: Value for the iso-surface
        interpolate: Whether to interpolate values (default: True)
        regularise: Whether to regularise the surface (default: True)

    Returns:
        SurfaceDataSet containing the isoSurface

    Example:
        >>> from pyOFTools.surfaces import create_iso_surface
        >>>
        >>> # Create iso-surface where alpha.water = 0.5 (interface)
        >>> interface = create_iso_surface(
        ...     "interface",
        ...     mesh,
        ...     field=alpha_field,
        ...     iso_field_name="alpha.water",
        ...     iso_value=0.5
        ... )
    """

    config = SampledIsoSurfaceConfig(isoField=iso_field_name, isoValue=iso_value)

    iso_dict = config.to_foam_dict()

    surface = sampledSurface.New(Word(name), mesh, iso_dict)
    surface.update()

    surfData = SurfaceDataSet(name=name, field=field, geometry=SampledSurfaceAdapter(surface))

    return surfData
