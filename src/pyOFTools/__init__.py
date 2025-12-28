"""
pyOFTools - Python tools for OpenFOAM

A collection of Python utilities and tools for working with OpenFOAM.
"""

__version__ = "0.1.0"
__author__ = "Henning Scheufler"
__email__ = "henning.scheufler@dlr.de"

# Import main modules that work standalone

# Import geometry adapters
from .geometry import SampledSurfaceAdapter, SampledSetAdapter

# Import surface mesh support modules
from . import surfaces
from . import interpolation

# Import set sampling modules
from . import sets
from . import set_interpolation

# Re-export commonly used surface creation functions
from .surfaces import (
    create_plane_surface,
    create_patch_surface,
    create_cutting_plane,
    create_iso_surface,
)

# Re-export interpolation utilities
from .interpolation import SurfaceInterpolator, create_interpolated_dataset

# Re-export set creation functions
from .sets import (
    create_uniform_set,
    create_cloud_set,
    create_polyline_set,
    create_circle_set,
)

# Re-export set interpolation utilities
from .set_interpolation import SetInterpolator, create_set_dataset

__all__ = [
    # Geometry adapters
    "SampledSurfaceAdapter",
    "SampledSetAdapter",
    # Modules
    "surfaces",
    "interpolation",
    "sets",
    "set_interpolation",
    # Surface creation functions
    "create_plane_surface",
    "create_patch_surface",
    "create_cutting_plane",
    "create_iso_surface",
    # Surface interpolation utilities
    "SurfaceInterpolator",
    "create_interpolated_dataset",
    # Set creation functions
    "create_uniform_set",
    "create_cloud_set",
    "create_polyline_set",
    "create_circle_set",
    # Set interpolation utilities
    "SetInterpolator",
    "create_set_dataset",
]
