from typing import Callable
import pybFoam
from pybFoam import volScalarField, Info
from pyOFTools.datasets import InternalDataSet
from typing import Callable, List





class postProcess():

    def __init__(self,mesh: pybFoam.fvMesh):
        self.mesh = mesh
        
    def execute(self):
        # self.csv1.write_data(self.mesh.time().value(),self.f.compute())
        alpha = volScalarField.from_registry(self.mesh,"alpha.water")
        Info(f"alpha[internalField][0]: {alpha.internalField()[0]}")

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
