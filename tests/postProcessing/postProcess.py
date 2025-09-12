from typing import Callable
import pybFoam
from pybFoam import volScalarField, Info
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from typing import Callable, List
from pyOFTools.writer import CSVWriter
from pyOFTools.aggregators import VolIntegrate
from pyOFTools.workflow import WorkFlow


class postProcess:
    def __init__(self, mesh: pybFoam.fvMesh):
        self.mesh = mesh
        self.volAlpha = CSVWriter(file_path="vol_alpha.csv")
        self.volAlpha.create_file()

    def execute(self):
        pass

    def write(self):
        alpha = volScalarField.from_registry(self.mesh, "alpha.water")
        workflow = WorkFlow(
            inputs=[
                InternalDataSet(
                    alpha["internalField"], geometry=FvMeshInternalAdapter(self.mesh)
                )
            ]
        ).then(VolIntegrate())
        self.volAlpha.write_data(self.mesh.time().value(), workflow)

    def end(self):
        pass
