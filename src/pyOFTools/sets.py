"""
Convenience utilities for creating common sampledSet types.

This module provides factory functions for easily creating different types
of sampled sets (lines, curves, point clouds) without dealing with OpenFOAM
dictionary setup directly.
"""

from __future__ import annotations

from typing import List, Literal, Tuple, Union

from pybFoam import Word, fvMesh, volScalarField, volSymmTensorField, volTensorField, volVectorField
from pybFoam.sampling import (
    CircleSetConfig,
    CloudSetConfig,
    PolyLineSetConfig,
    UniformSetConfig,
    meshSearch,
    sampledSet,
)

from .datasets import PointDataSet
from .set_interpolation import create_set_dataset

GeoFieldType = Union[volScalarField, volVectorField, volTensorField, volSymmTensorField]
InterpolationScheme = Literal["cell", "cellPoint", "cellPointFace"]


def _to_tuple(point: Union[Tuple[float, float, float], List[float]]) -> Tuple[float, float, float]:
    """Convert point from list or tuple to tuple."""
    if isinstance(point, (list, tuple)):
        if len(point) != 3:
            raise ValueError(f"Point must have exactly 3 coordinates, got {len(point)}")
        return (point[0], point[1], point[2])
    raise TypeError(f"Point must be tuple or list, got {type(point)}")


def create_uniform_set(
    mesh: fvMesh,
    name: str,
    start: Union[Tuple[float, float, float], List[float]],
    end: Union[Tuple[float, float, float], List[float]],
    n_points: int,
    field: GeoFieldType,
    axis: str = "distance",
    scheme: InterpolationScheme = "cellPoint",
) -> PointDataSet:
    """
    Create a uniform (straight line) sampledSet with interpolated field values.

    Creates a straight line with uniformly distributed sample points between
    start and end positions, and interpolates the provided field onto those points.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the set
        start: Start point (x, y, z)
        end: End point (x, y, z)
        n_points: Number of sample points
        field: Volume field to interpolate (volScalarField, volVectorField, etc.)
        axis: Output axis type. Options:
            - "distance": cumulative distance along line (default)
            - "x", "y", "z": coordinate value
            - "xyz": 3D coordinates
        scheme: Interpolation scheme (default: "cellPoint")

    Returns:
        PointDataSet containing interpolated field values and geometry

    Example:
        >>> from pybFoam import fvMesh, Time, volScalarField
        >>> from pyOFTools.sets import create_uniform_set
        >>>
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>> p = volScalarField.read_field(mesh, "p")
        >>>
        >>> # Create horizontal line with pressure values
        >>> dataset = create_uniform_set(
        ...     mesh,
        ...     "centerline",
        ...     start=(0.0, 0.5, 0.5),
        ...     end=(1.0, 0.5, 0.5),
        ...     n_points=100,
        ...     field=p
        ... )
        >>>
        >>> # Access interpolated values and geometry
        >>> positions = dataset.geometry.positions
        >>> pressures = dataset.field
        >>> distances = dataset.geometry.distance
    """
    start = _to_tuple(start)
    end = _to_tuple(end)

    if n_points <= 0:
        raise ValueError(f"n_points must be positive, got {n_points}")

    # Create config using pydantic model
    config = UniformSetConfig(axis=axis, start=list(start), end=list(end), nPoints=n_points)

    # Convert to OpenFOAM dictionary
    set_dict = config.to_foam_dict()

    # Create mesh search engine
    search = meshSearch(mesh)

    # Create sampledSet
    sampled_set = sampledSet.New(Word(name), mesh, search, set_dict)

    # Create dataset with interpolated field
    return create_set_dataset(sampled_set, field, name, scheme=scheme, mask_invalid=True)


def create_cloud_set(
    mesh: fvMesh,
    name: str,
    points: List[Tuple[float, float, float]],
    field: GeoFieldType,
    axis: str = "xyz",
    scheme: InterpolationScheme = "cellPoint",
) -> PointDataSet:
    """
    Create a cloud (arbitrary points) sampledSet with interpolated field values.

    Creates a set of sample points at arbitrary user-specified locations.
    Useful for validation against experimental probe locations or specific
    points of interest.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the set
        points: List of sample point coordinates [(x,y,z), ...]
        field: Volume field to interpolate
        axis: Output axis type (usually "xyz" for clouds)
        scheme: Interpolation scheme (default: "cellPoint")

    Returns:
        PointDataSet containing interpolated field values and geometry

    Example:
        >>> from pyOFTools.sets import create_cloud_set
        >>>
        >>> # Sample at specific probe locations
        >>> probes = create_cloud_set(
        ...     mesh,
        ...     "probes",
        ...     points=[
        ...         (0.1, 0.2, 0.3),
        ...         (0.5, 0.5, 0.5),
        ...         (0.8, 0.7, 0.6)
        ...     ]
        ... )
    """
    if not points:
        raise ValueError("points list cannot be empty")

    # Convert all points to lists of floats
    points_list = [list(_to_tuple(p)) for p in points]

    # Create config
    config = CloudSetConfig(axis=axis, points=points_list)

    # Convert to OpenFOAM dictionary
    set_dict = config.to_foam_dict()

    # Create mesh search engine
    search = meshSearch(mesh)

    # Create sampledSet
    sampled_set = sampledSet.New(Word(name), mesh, search, set_dict)

    # Create dataset with interpolated field
    return create_set_dataset(sampled_set, field, name, scheme=scheme, mask_invalid=True)


def create_polyline_set(
    mesh: fvMesh,
    name: str,
    points: List[Tuple[float, float, float]],
    n_points: int,
    field: GeoFieldType,
    axis: str = "distance",
    scheme: InterpolationScheme = "cellPoint",
) -> PointDataSet:
    """
    Create a polyLine (multi-segment) sampledSet with interpolated field values.

    Creates a path through multiple knot points with sample points distributed
    along all segments. Useful for sampling along curved paths or through
    complex geometry.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the set
        points: List of knot points defining the polyline path
        n_points: Total number of sample points (distributed across all segments)
        field: Volume field to interpolate
        axis: Output axis type (usually "distance")
        scheme: Interpolation scheme (default: "cellPoint")

    Returns:
        PointDataSet containing interpolated field values and geometry

    Example:
        >>> from pyOFTools.sets import create_polyline_set
        >>>
        >>> # Create L-shaped path
        >>> path = create_polyline_set(
        ...     mesh,
        ...     "Lpath",
        ...     points=[
        ...         (0.0, 0.0, 0.5),  # Start
        ...         (1.0, 0.0, 0.5),  # Corner
        ...         (1.0, 1.0, 0.5)   # End
        ...     ],
        ...     n_points=100
        ... )
    """
    if len(points) < 2:
        raise ValueError("polyLine requires at least 2 points")

    if n_points <= 0:
        raise ValueError(f"n_points must be positive, got {n_points}")

    # Convert all points to lists
    points_list = [list(_to_tuple(p)) for p in points]

    # Create config
    config = PolyLineSetConfig(axis=axis, points=points_list, nPoints=n_points)

    # Convert to OpenFOAM dictionary
    set_dict = config.to_foam_dict()

    # Create mesh search engine
    search = meshSearch(mesh)

    # Create sampledSet
    sampled_set = sampledSet.New(Word(name), mesh, search, set_dict)

    # Create dataset with interpolated field
    return create_set_dataset(sampled_set, field, name, scheme=scheme, mask_invalid=True)


def create_circle_set(
    mesh: fvMesh,
    name: str,
    origin: Tuple[float, float, float],
    circle_axis: Tuple[float, float, float],
    start_point: Tuple[float, float, float],
    d_theta: float,
    field: GeoFieldType,
    axis: str = "distance",
    scheme: InterpolationScheme = "cellPoint",
) -> PointDataSet:
    """
    Create a circle sampledSet with interpolated field values.

    Creates a circular sampling path. The circle is defined by its center (origin),
    normal direction (circle_axis), and a starting point on the circumference.

    Args:
        mesh: OpenFOAM mesh
        name: Name for the set
        origin: Center point of circle (x, y, z)
        circle_axis: Normal vector of circle plane (nx, ny, nz)
        start_point: Starting point on circle circumference (defines radius)
        d_theta: Angular increment in degrees (default: 10.0)
        field: Volume field to interpolate
        axis: Output axis type (usually "distance")
        scheme: Interpolation scheme (default: "cellPoint")

    Returns:
        PointDataSet containing interpolated field values and geometry

    Example:
        >>> from pyOFTools.sets import create_circle_set
        >>>
        >>> # Create horizontal circle at z=0.5 with radius 0.3
        >>> circle = create_circle_set(
        ...     mesh,
        ...     "circle",
        ...     origin=(0.5, 0.5, 0.5),
        ...     circle_axis=(0.0, 0.0, 1.0),  # Normal to xy-plane
        ...     start_point=(0.8, 0.5, 0.5),  # Radius = 0.3
        ...     d_theta=5.0,
        ...     field=p
        ... )
    """
    origin = _to_tuple(origin)
    circle_axis = _to_tuple(circle_axis)
    start_point = _to_tuple(start_point)

    if d_theta <= 0:
        raise ValueError(f"d_theta must be positive, got {d_theta}")

    # Create config
    config = CircleSetConfig(
        axis=axis,
        origin=list(origin),
        circleAxis=list(circle_axis),
        startPoint=list(start_point),
        dTheta=d_theta,
    )

    # Convert to OpenFOAM dictionary
    set_dict = config.to_foam_dict()

    # Create mesh search engine
    search = meshSearch(mesh)

    # Create sampledSet
    sampled_set = sampledSet.New(Word(name), mesh, search, set_dict)

    # Create dataset with interpolated field
    return create_set_dataset(sampled_set, field, name, scheme=scheme, mask_invalid=True)
