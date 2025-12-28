"""
Convenience utilities for creating common surface types.

This module provides factory functions for easily creating different types
of sampled surfaces without dealing with OpenFOAM dictionary setup directly.
"""

from typing import Dict, List, Tuple, Union

from pybFoam import Word, dictionary, fvMesh, vector, wordList
from pybFoam.sampling import sampledSurface


def _to_tuple(
    point: Union[Tuple[float, float, float], Dict[str, float]],
) -> Tuple[float, float, float]:
    """Convert point from dict or tuple to tuple."""
    if isinstance(point, dict):
        return (point.get("x", 0.0), point.get("y", 0.0), point.get("z", 0.0))
    return point


def create_plane_surface(
    mesh: "fvMesh",
    name: str,
    point: Tuple[float, float, float],
    normal: Tuple[float, float, float],
    triangulate: bool = False,
) -> "sampledSurface":
    """
    Create a plane surface for sampling.

    Creates a plane surface defined by a point and normal vector that
    intersects the mesh. This is useful for extracting 2D slices of 3D data.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the surface
        point: Point on the plane (x, y, z)
        normal: Normal vector (nx, ny, nz) - will be normalized automatically
        triangulate: Whether to triangulate the surface (default: False)

    Returns:
        sampledPlane surface instance

    Example:
        >>> from pybFoam import fvMesh, Time
        >>> from pyOFTools.surfaces import create_plane_surface
        >>>
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>>
        >>> # Create a vertical plane at x=0.5
        >>> surface = create_plane_surface(
        ...     mesh,
        ...     "midPlane",
        ...     point=(0.5, 0, 0),
        ...     normal=(1, 0, 0)
        ... )
    """

    # Convert dict to tuple if needed
    point = _to_tuple(point)
    normal = _to_tuple(normal)

    plane_dict = dictionary()
    plane_dict.set("type", Word("plane"))
    plane_dict.set("point", vector(*point))
    plane_dict.set("normal", vector(*normal))
    if triangulate:
        plane_dict.set("triangulate", True)

    surface = sampledSurface.New(Word(name), mesh, plane_dict)
    surface.update()
    return surface


def create_patch_surface(
    mesh: "fvMesh", name: str, patches: List[str], triangulate: bool = False
) -> "sampledSurface":
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
    mesh: "fvMesh",
    name: str,
    point: Tuple[float, float, float],
    normal: Tuple[float, float, float],
    interpolate: bool = True,
) -> "sampledSurface":
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
    mesh: "fvMesh",
    name: str,
    field_name: str,
    iso_value: float,
    interpolate: bool = True,
    regularise: bool = True,
) -> "sampledSurface":
    """
    Create an iso-surface of a scalar field.

    An iso-surface is the 3D equivalent of a contour line, representing
    all points where a field has a specific value.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the surface
        field_name: Name of the scalar field to create iso-surface from
        iso_value: Value for the iso-surface
        interpolate: Whether to interpolate values (default: True)
        regularise: Whether to regularise the surface (default: True)

    Returns:
        isoSurface surface instance

    Example:
        >>> from pyOFTools.surfaces import create_iso_surface
        >>>
        >>> # Create iso-surface where alpha.water = 0.5 (interface)
        >>> interface = create_iso_surface(
        ...     mesh,
        ...     "interface",
        ...     field_name="alpha.water",
        ...     iso_value=0.5
        ... )
    """

    iso_dict = dictionary()
    iso_dict.set("type", Word("isoSurface"))
    iso_dict.set("isoField", Word(field_name))
    iso_dict.set("isoValue", iso_value)
    if not interpolate:
        iso_dict.set("interpolate", False)
    if not regularise:
        iso_dict.set("regularise", False)

    surface = sampledSurface.New(Word(name), mesh, iso_dict)
    surface.update()
    return surface
