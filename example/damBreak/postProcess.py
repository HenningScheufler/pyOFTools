from typing import Callable
import pybFoam
from pybFoam import volScalarField, Info
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from typing import Callable, List
from pyOFTools.writer import CSVWriter
from pyOFTools.aggregators import VolIntegrate
from pyOFTools.binning import Directional
from pyOFTools.workflow import WorkFlow


class postProcess:
    def __init__(self, mesh: pybFoam.fvMesh):
        self.mesh = mesh
        self.volAlpha = CSVWriter(file_path="postProcessing/vol_alpha.csv")
        self.volAlpha.create_file()
        self.mass = CSVWriter(file_path="postProcessing/mass.csv")
        self.mass.create_file()

        self.mass_dist_height = CSVWriter(
            file_path="postProcessing/mass_dist_height.csv"
        )
        self.mass_dist_height.create_file()

    def execute(self):
        pass

    def write(self):
        alpha = volScalarField.from_registry(self.mesh, "alpha.water")
        w_alpha = WorkFlow(
            initial_dataset=InternalDataSet(
                name="alpha_water",
                field=alpha["internalField"],
                geometry=FvMeshInternalAdapter(self.mesh),
            )
        ).then(VolIntegrate())
        self.volAlpha.write_data(time=self.mesh.time().value(), workflow=w_alpha)

        rho = volScalarField.from_registry(self.mesh, "rho")
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
                    bins=[0.0, 0.146, 0.292, 0.438, 0.584],
                    direction=(1, 0, 0),
                    origin=(0, 0, 0),
                )
            )
            .then(VolIntegrate())
        )
        self.mass.write_data(time=self.mesh.time().value(), workflow=w_mass)

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
                    bins=[0.0, 0.146, 0.292, 0.438, 0.584],
                    direction=(0, 1, 0),
                    origin=(0, 0, 0),
                )
            )
            .then(VolIntegrate())
        )
        self.mass_dist_height.write_data(
            time=self.mesh.time().value(), workflow=w_mass_height
        )

    def end(self):
        pass
