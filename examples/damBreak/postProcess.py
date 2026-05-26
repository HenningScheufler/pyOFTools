"""In-situ monitors for the damBreak case.

Loaded by OpenFOAM's ``pyPostProcessing`` function object — see the
``pyPostProcessing`` block in ``system/controlDict``. The ``pyClassName``
there is ``postProcess``, so OpenFOAM looks up the module-level
``postProcess`` object below, calls it with the mesh to get a runner, and
drives ``execute`` / ``write`` / ``end`` on that runner on its own schedule.

Each ``@Table`` decorator below registers one CSV output. Add a new one and
the next run will produce a new file under ``postProcessing/`` — no other
plumbing needed.
"""

from pyOFTools.aggregators import Mean, Sum, VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.builders import area, field, iso_surface, plane, sample
from pyOFTools.postprocessor import PostProcessorBase

# ``base_path`` is concatenated with each filename verbatim, so it needs the
# trailing slash. Relative path → resolves under the solver's cwd, which is
# the case directory.
postProcess = PostProcessorBase(base_path="postProcessing/")


@postProcess.Table("water_volume.csv")
def water_volume(m):
    # Total volume of liquid in the tank — a conservation check.
    return field(m, "alpha.water") | VolIntegrate(name="water_volume")


@postProcess.Table("interface_area.csv")
def interface_area(m):
    # Area of the α = 0.5 iso-surface ≈ the gas–liquid interface. Grows when
    # the wave breaks up, drops when it coalesces.
    return iso_surface(m, "alpha.water", 0.5) | area() | Sum(name="interface_area")


@postProcess.Table("mass_profile_x.csv")
def mass_profile_x(m):
    # Mass binned along the tank's x-axis. ``rho`` only exists once the
    # thermophysical model has initialised, i.e. at the first solver step.
    edges = [0.0, 0.146, 0.292, 0.438, 0.584]
    return (
        field(m, "rho")
        | Directional(bins=edges, direction=(1.0, 0.0, 0.0), origin=(0.0, 0.0, 0.0))
        | VolIntegrate(name="mass")
    )


@postProcess.Table("mean_p_midplane.csv")
def mean_p_midplane(m):
    # Average pressure on a horizontal plane halfway up the initial water
    # column. ``sample`` interpolates the volume field onto the plane.
    return (
        plane(m, point=(0.0, 0.146, 0.0), normal=(0.0, 1.0, 0.0))
        | sample(m, "p")
        | Mean(name="mean_p_midplane")
    )