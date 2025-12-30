import pybFoam
from pybFoam import scalarField, volScalarField

from pyOFTools.aggregators import Sum, VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from pyOFTools.surfaces import create_iso_surface
from pyOFTools.workflow import WorkFlow
from pyOFTools.writer import CSVWriter


class postProcess:
    def __init__(self, mesh: pybFoam.fvMesh):
        # Store mesh reference for field access
        self.mesh = mesh
        # Set up CSV writers for each output file
        self.volAlpha = CSVWriter(file_path="postProcessing/vol_alpha.csv")
        self.volAlpha.create_file()  # Create CSV file for volume of alpha.water
        self.mass = CSVWriter(file_path="postProcessing/mass.csv")
        self.mass.create_file()  # Create CSV file for mass distribution (width)
        self.mass_dist_height = CSVWriter(file_path="postProcessing/mass_dist_height.csv")
        self.mass_dist_height.create_file()  # Create CSV file for mass distribution (height)
        self.free_surface_area = CSVWriter(file_path="postProcessing/free_surface_area.csv")
        self.free_surface_area.create_file()  # Create CSV file for free surface area

    def execute(self):
        # This method can be used for additional execution steps if needed
        pass

    def write(self):
        # --- Calculate and write volume of alpha.water ---
        # Get alpha.water field from OpenFOAM registry
        alpha = volScalarField.from_registry(self.mesh, "alpha.water")
        # Set up workflow: wrap field in InternalDataSet, adapt mesh, then integrate volume
        w_alpha = WorkFlow(
            initial_dataset=InternalDataSet(
                name="alpha_water",
                field=alpha["internalField"],
                geometry=FvMeshInternalAdapter(self.mesh),
            )
        ).then(VolIntegrate())  # Integrate over the volume
        # Write result to CSV, including current simulation time
        self.volAlpha.write_data(time=self.mesh.time().value(), workflow=w_alpha)

        # --- Calculate and write mass distribution along width ---
        # Get density field from OpenFOAM registry
        rho = volScalarField.from_registry(self.mesh, "rho")
        # Set up workflow: bin field along x-direction, then integrate mass in each bin
        w_mass = (
            WorkFlow(
                initial_dataset=InternalDataSet(
                    name="rho",
                    field=rho["internalField"],
                    geometry=FvMeshInternalAdapter(self.mesh),
                )
            )
            .then(
                Directional(
                    bins=[0.0, 0.146, 0.292, 0.438, 0.584],  # Bin edges along x-direction
                    direction=(1, 0, 0),
                    origin=(0, 0, 0),
                )
            )
            .then(VolIntegrate())  # Integrate mass in each bin
        )
        # Write result to CSV, including current simulation time
        self.mass.write_data(time=self.mesh.time().value(), workflow=w_mass)

        # --- Calculate and write mass distribution along height ---
        # Set up workflow: bin field along y-direction, then integrate mass in each bin
        w_mass_height = (
            WorkFlow(
                initial_dataset=InternalDataSet(
                    name="rho",
                    field=rho["internalField"],
                    geometry=FvMeshInternalAdapter(self.mesh),
                )
            )
            .then(
                Directional(
                    bins=[0.0, 0.146, 0.292, 0.438, 0.584],  # Bin edges along y-direction
                    direction=(0, 1, 0),
                    origin=(0, 0, 0),
                )
            )
            .then(VolIntegrate())
        )
        # Write result to CSV, including current simulation time
        self.mass_dist_height.write_data(time=self.mesh.time().value(), workflow=w_mass_height)

        iso_surface = create_iso_surface(
            name="freeSurface",
            mesh=self.mesh,
            field=scalarField([0.0]),  # Dummy field, not used for area calculation
            iso_field_name="alpha.water",
            iso_value=0.5,
        )
        iso_surface.field = iso_surface.geometry.face_area_magnitudes

        w_surface_area = WorkFlow(initial_dataset=iso_surface).then(Sum())  # Integrate surface area

        self.free_surface_area.write_data(time=self.mesh.time().value(), workflow=w_surface_area)

    def end(self):
        # This method can be used for cleanup or finalization if needed
        pass
