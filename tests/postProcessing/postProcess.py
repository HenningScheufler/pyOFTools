from typing import Any

import pybFoam

from pyOFTools.aggregators import Sum, VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.builders import area, field, iso_surface, residuals
from pyOFTools.postprocessor import PostProcessorBase, PostProcessorRunner

# Create post-processor instance
postProcess = PostProcessorBase()


@postProcess.Table("vol_alpha.csv")
def vol_alpha(mesh: pybFoam.fvMesh) -> Any:
    """Calculate volume of alpha.water field."""
    return field(mesh, "alpha.water") | VolIntegrate()


@postProcess.Table("mass.csv")
def mass_x(mesh: pybFoam.fvMesh) -> Any:
    """Calculate mass distribution along x-direction (width)."""
    return (
        field(mesh, "rho")
        | Directional(
            bins=[0.0, 0.146, 0.292, 0.438, 0.584],
            direction=(1, 0, 0),
            origin=(0, 0, 0),
        )
        | VolIntegrate()
    )


@postProcess.Table("mass_dist_height.csv")
def mass_y(mesh: pybFoam.fvMesh) -> Any:
    """Calculate mass distribution along y-direction (height)."""
    return (
        field(mesh, "rho")
        | Directional(
            bins=[0.0, 0.146, 0.292, 0.438, 0.584],
            direction=(0, 1, 0),
            origin=(0, 0, 0),
        )
        | VolIntegrate()
    )


@postProcess.Table("free_surface_area.csv")
def free_surface_area(mesh: pybFoam.fvMesh) -> Any:
    """Calculate free surface area from iso-surface of alpha.water = 0.5."""
    return iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()


@postProcess.Table("residuals.csv")
def solver_residuals(mesh: pybFoam.fvMesh) -> Any:
    """Track solver residuals and performance."""
    return residuals(mesh)


def build(mesh: pybFoam.fvMesh) -> PostProcessorRunner:
    """
    Factory function to create post-processor instance.

    This is called by OpenFOAM to instantiate the function object.
    """
    return postProcess(mesh)
