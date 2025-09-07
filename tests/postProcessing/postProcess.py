from typing import Callable
import pybFoam
from pybFoam import volScalarField, Info
from pyOFTools.datasets import InternalDataSet
from pyOFTools.geometry import FvMeshInternalAdapter
from pyOFTools.aggregators import Max, Min, Mean, Sum, VolIntegrate
from pyOFTools.spatial_selectors import Box
from pyOFTools.writer import CSVWriter
from typing import Callable, List
from pyOFTools.workflow import create_workflow


WorkFlow = create_workflow()


class postProcess:
    def __init__(self, mesh: pybFoam.fvMesh):
        self.mesh = mesh
        self.csv1 = CSVWriter(file_path="intAlpha.csv")

    def execute(self):
        # self.csv1.write_data(self.mesh.time().value(),self.f.compute())
        alpha = volScalarField.from_registry(self.mesh, "alpha.water")
        Info(f"alpha[internalField][0]: {alpha.internalField()[0]}")
        alpha_internal = InternalDataSet(
            name="alpha",
            field=alpha["internalField"],
            geometry=FvMeshInternalAdapter(self.mesh),
        )

        workflow = (
            WorkFlow(initial_dataset=alpha_internal)
            .then(Box(min=(-1, -1, -1), max=(0.292, 1, 1)))
            .then(VolIntegrate())
        )

        self.csv1.write_data(
            self.mesh.time().value(),
            workflow,
        )

    def write(self):
        pass

    def end(self):
        pass


# ppf = postProcessFunctions(mesh)
# ppb = pybFoam.postProcess.postProcessBuilder()

# @ppf.time_series()
# def add_force():
#     return [time_series.Force()]


# csv1 = time_series.csvTimeSeries(
#     mesh, writeFrequency=time_series.time_step(1), functions=[f]
# )
# csv1.execute()

# sets
