"""
Surface field interpolation utilities.

This module provides tools for interpolating volume fields onto surfaces,
separating interpolation logic from geometry to allow flexible sampling strategies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

from pybFoam import (
    Word,
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

if TYPE_CHECKING:
    from .datasets import SurfaceDataSet

VolFieldType = Union[volScalarField, volVectorField, volTensorField, volSymmTensorField]
InterpolatedFieldType = Union[scalarField, vectorField, tensorField, symmTensorField]


InterpolationScheme = Literal["cell", "cellPoint", "cellPointFace"]


class SurfaceInterpolator:
    """
    Handles interpolation of volume fields onto surfaces.

    This class separates the interpolation logic from surface geometry,
    allowing the same surface to be used with different fields and
    interpolation schemes without rebuilding the surface.

    Attributes:
        scheme: OpenFOAM interpolation scheme name
        use_point_data: Whether to interpolate to surface points (True) or face centers (False)

    Example:
        >>> from pybFoam import fvMesh, Time, volScalarField
        >>> from pybFoam.sampling import sampledPlane
        >>> from pyOFTools.interpolation import SurfaceInterpolator
        >>>
        >>> # Setup mesh and surface
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>> surface = create_plane_surface(mesh, "plane", (0.5, 0, 0), (1, 0, 0))
        >>>
        >>> # Create interpolator
        >>> interpolator = SurfaceInterpolator(scheme="cellPoint", use_point_data=False)
        >>>
        >>> # Interpolate field
        >>> field = volScalarField.from_registry(mesh, "p")
        >>> interpolated_values = interpolator.interpolate(field, surface)
    """

    def __init__(self, scheme: InterpolationScheme = "cellPoint", use_point_data: bool = False):
        """
        Initialize interpolator.

        Args:
            scheme: OpenFOAM interpolation scheme. Options:
                - "cell": Use cell values directly
                - "cellPoint": Interpolate from cells to points
                - "cellPointFace": More accurate interpolation through face values
            use_point_data: If True, interpolate to surface points;
                          if False (default), interpolate to face centers
        """
        self.scheme = scheme
        self.use_point_data = use_point_data

    def interpolate(
        self,
        field: VolFieldType,
        surface: sampling.sampledSurface,
    ) -> InterpolatedFieldType:
        """
        Interpolate a volume field onto a surface.

        Args:
            field: OpenFOAM volume field to interpolate
            surface: sampledSurface to interpolate onto

        Returns:
            Interpolated field values on the surface (on faces or points
            depending on use_point_data)

        Raises:
            TypeError: If field type is not supported
        """
        # Determine field type and create appropriate interpolator
        if isinstance(field, volScalarField):
            interp = sampling.interpolationScalar.New(Word(self.scheme), field)
            if self.use_point_data:
                return sampling.sampleOnPointsScalar(surface, interp)
            else:
                return sampling.sampleOnFacesScalar(surface, interp)

        elif isinstance(field, volVectorField):
            interp_vec = sampling.interpolationVector.New(Word(self.scheme), field)
            if self.use_point_data:
                return sampling.sampleOnPointsVector(surface, interp_vec)
            else:
                return sampling.sampleOnFacesVector(surface, interp_vec)

        elif isinstance(field, volTensorField):
            interp_tens = sampling.interpolationTensor.New(Word(self.scheme), field)
            if self.use_point_data:
                return sampling.sampleOnPointsTensor(surface, interp_tens)
            else:
                return sampling.sampleOnFacesTensor(surface, interp_tens)

        elif isinstance(field, volSymmTensorField):
            interp_symm = sampling.interpolationSymmTensor.New(Word(self.scheme), field)
            if self.use_point_data:
                return sampling.sampleOnPointsSymmTensor(surface, interp_symm)
            else:
                return sampling.sampleOnFacesSymmTensor(surface, interp_symm)

        else:
            raise TypeError(
                f"Unsupported field type: {type(field)}. "
                "Supported types: volScalarField, volVectorField, "
                "volTensorField, volSymmTensorField"
            )


def create_interpolated_dataset(
    field: VolFieldType,
    surface: sampling.sampledSurface,
    interpolator: SurfaceInterpolator,
    name: Optional[str] = None,
) -> SurfaceDataSet:
    """
    Convenience function to create a SurfaceDataSet with interpolated values.

    This function combines surface geometry and field interpolation into a single
    dataset object that can be used with the pyOFTools workflow system.

    Args:
        field: Volume field to interpolate
        surface: Surface to interpolate onto
        interpolator: Interpolator instance to use
        name: Name for the dataset (defaults to field name)

    Returns:
        SurfaceDataSet with interpolated field values and geometry

    Example:
        >>> from pyOFTools.interpolation import create_interpolated_dataset, SurfaceInterpolator
        >>> from pyOFTools.surfaces import create_plane_surface
        >>>
        >>> # Create surface and interpolator
        >>> surface = create_plane_surface(mesh, "plane", (0.5, 0, 0), (1, 0, 0))
        >>> interpolator = SurfaceInterpolator(scheme="cellPoint")
        >>>
        >>> # Create dataset
        >>> field = volScalarField.from_registry(mesh, "alpha.water")
        >>> dataset = create_interpolated_dataset(field, surface, interpolator, name="alpha")
        >>>
        >>> # Use in workflow
        >>> from pyOFTools.workflow import WorkFlow
        >>> from pyOFTools.aggregators import Sum
        >>> workflow = WorkFlow(initial_dataset=dataset).then(Sum())
        >>> result = workflow.execute()
    """
    from .datasets import SurfaceDataSet
    from .geometry import SampledSurfaceAdapter

    interpolated_field = interpolator.interpolate(field, surface)

    # Get field name if not provided
    if name is None:
        name = str(field.name()) if hasattr(field, "name") else "unknown"

    return SurfaceDataSet(
        name=name, field=interpolated_field, geometry=SampledSurfaceAdapter(surface)
    )
