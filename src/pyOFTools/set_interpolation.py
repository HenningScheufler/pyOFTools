"""
Set field interpolation utilities.

This module provides tools for interpolating volume fields onto sampledSets
(lines, curves, point clouds), separating interpolation logic from geometry
to allow flexible sampling strategies.
"""

from __future__ import annotations

from typing import Literal, Union

from pybFoam import (
    Word,
    boolList,
    sampling,
    scalarField,
    symmTensorField,
    tensorField,
    vectorField,
    volScalarField,
    volSymmTensorField,
    volTensorField,
    volVectorField,
)

VolFieldType = Union[volScalarField, volVectorField, volTensorField, volSymmTensorField]
InterpolatedFieldType = Union[scalarField, vectorField, tensorField, symmTensorField]

from .datasets import PointDataSet
from .geometry import SampledSetAdapter

InterpolationScheme = Literal["cell", "cellPoint", "cellPointFace"]


class SetInterpolator:
    """
    Handles interpolation of volume fields onto sampledSets.

    This class separates the interpolation logic from set geometry,
    allowing the same set to be used with different fields and
    interpolation schemes without rebuilding the set.

    Attributes:
        scheme: OpenFOAM interpolation scheme name

    Example:
        >>> from pybFoam import fvMesh, Time, volScalarField
        >>> from pybFoam.sampling import sampledSet
        >>> from pyOFTools.set_interpolation import SetInterpolator
        >>> from pyOFTools.sets import create_uniform_set
        >>>
        >>> # Setup mesh and set
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>> line = create_uniform_set(mesh, "line", (0,0,0), (1,0,0), 50)
        >>>
        >>> # Create interpolator
        >>> interpolator = SetInterpolator(scheme="cellPoint")
        >>>
        >>> # Interpolate field
        >>> field = volScalarField.read_field(mesh, "p")
        >>> interpolated_values = interpolator.interpolate(field, line)
    """

    def __init__(self, scheme: InterpolationScheme = "cellPoint"):
        """
        Initialize interpolator.

        Args:
            scheme: OpenFOAM interpolation scheme. Options:
                - "cell": Use cell values directly
                - "cellPoint": Interpolate from cells to points (recommended)
                - "cellPointFace": More accurate interpolation through face values
        """
        valid_schemes = ["cell", "cellPoint", "cellPointFace"]
        if scheme not in valid_schemes:
            raise ValueError(
                f"Invalid interpolation scheme '{scheme}'. "
                f"Valid options are: {', '.join(valid_schemes)}"
            )

        self.scheme = scheme

    def interpolate(
        self,
        field: VolFieldType,
        sampled_set: sampling.sampledSet,
    ) -> InterpolatedFieldType:
        """
        Interpolate a volume field onto a sampledSet.

        Args:
            field: OpenFOAM volume field to interpolate
            sampled_set: sampledSet to interpolate onto

        Returns:
            Interpolated field values at sample points

        Raises:
            TypeError: If field type is not supported
        """
        # Determine field type and create appropriate interpolator
        if isinstance(field, volScalarField):
            interp = sampling.interpolationScalar.New(Word(self.scheme), field)
            return sampling.sampleSetScalar(sampled_set, interp)

        elif isinstance(field, volVectorField):
            interp = sampling.interpolationVector.New(Word(self.scheme), field)
            return sampling.sampleSetVector(sampled_set, interp)

        elif isinstance(field, volTensorField):
            interp = sampling.interpolationTensor.New(Word(self.scheme), field)
            return sampling.sampleSetTensor(sampled_set, interp)

        elif isinstance(field, volSymmTensorField):
            interp = sampling.interpolationSymmTensor.New(Word(self.scheme), field)
            return sampling.sampleSetSymmTensor(sampled_set, interp)

        else:
            raise TypeError(
                f"Unsupported field type: {type(field).__name__}. "
                "Supported types: volScalarField, volVectorField, volTensorField, volSymmTensorField"
            )


def create_set_dataset(
    sampled_set: sampling.sampledSet,
    field: VolFieldType,
    name: str,
    scheme: InterpolationScheme = "cellPoint",
    mask_invalid: bool = True,
) -> PointDataSet:
    """
    Create a PointDataSet from a sampledSet and field.

    Convenience function that combines set geometry wrapping, field interpolation,
    and dataset creation into a single call.

    Args:
        sampled_set: OpenFOAM sampledSet instance
        field: Volume field to interpolate
        name: Name for the dataset
        scheme: Interpolation scheme (default: "cellPoint")
        mask_invalid: If True, create a mask for invalid points (default: True)

    Returns:
        PointDataSet containing interpolated field values and geometry

    Example:
        >>> from pybFoam import Time, fvMesh, volScalarField
        >>> from pyOFTools.sets import create_uniform_set
        >>> from pyOFTools.set_interpolation import create_set_dataset
        >>>
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>>
        >>> # Create line
        >>> line = create_uniform_set(mesh, "line", (0,0,0), (1,0,0), 50)
        >>>
        >>> # Read field
        >>> p = volScalarField.read_field(mesh, "p")
        >>>
        >>> # Create dataset in one step
        >>> dataset = create_set_dataset(line, p, "pressure_line")
        >>>
        >>> # Access data
        >>> positions = dataset.geometry.positions
        >>> values = dataset.field
    """
    # Create interpolator
    interpolator = SetInterpolator(scheme=scheme)

    # Interpolate field
    field_values = interpolator.interpolate(field, sampled_set)

    # Wrap geometry in adapter
    geometry = SampledSetAdapter(sampled_set)

    # Create mask if requested
    mask = None
    if mask_invalid:
        # Create mask for invalid points (cell ID == -1)
        cells = sampled_set.cells()
        mask = boolList([cell >= 0 for cell in cells])

    # Create and return PointDataSet
    return PointDataSet(name=name, field=field_values, geometry=geometry, mask=mask, groups=None)
