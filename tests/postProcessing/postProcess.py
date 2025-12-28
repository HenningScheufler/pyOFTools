import pybFoam
from pybFoam import volScalarField

from pyOFTools.aggregators import VolIntegrate
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from pyOFTools.workflow import WorkFlow
from pyOFTools.writer import CSVWriter


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
                InternalDataSet(alpha["internalField"], geometry=FvMeshInternalAdapter(self.mesh))
            ]
        ).then(VolIntegrate())
        self.volAlpha.write_data(self.mesh.time().value(), workflow)

    def end(self):
        pass
