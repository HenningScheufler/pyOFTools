import pybFoam

from pyOFTools.aggregators import Sum, VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.builders import field, iso_surface, residuals
from pyOFTools.postprocessor import PostProcessorBase


# Create post-processor instance
postProcess = PostProcessorBase()


@postProcess.Table("vol_alpha.csv")
def vol_alpha(mesh):
    """Calculate volume of alpha.water field."""
    return field(mesh, "alpha.water") | VolIntegrate()


@postProcess.Table("mass.csv")
def mass_x(mesh):
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
def mass_y(mesh):
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
def free_surface_area(mesh):
    """Calculate free surface area from iso-surface of alpha.water = 0.5."""
    return iso_surface(mesh, "alpha.water", 0.5) | Sum()


@postProcess.Table("solverPerformance.csv")
def solver_performance(mesh):
    """Track solver residuals and performance."""
    return residuals(mesh)


def build(mesh: pybFoam.fvMesh):
    """
    Factory function to create post-processor instance.
    
    This is called by OpenFOAM to instantiate the function object.
    """
    return postProcess(mesh)
