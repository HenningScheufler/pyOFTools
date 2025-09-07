from pybFoam import boolList, vector, mag, labelList
from typing import Union, Literal, Tuple, Annotated
from pydantic import BaseModel, Field
from .datasets import DataSets
from .node import Node
import numpy as np
import yaml


# --- Primitives ---
@Node.register()
class Directional(Node):
    type: Literal["directional"] = "directional"
    bins: list[float]
    direction: Tuple[float, float, float]
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def compute(self, dataset: DataSets) -> DataSets:
        positions = dataset.geometry.positions
        normal = vector(self.direction)
        normal = normal * (1.0 / mag(normal))
        distance = (positions - vector(self.origin)) & (vector(self.direction))
        np_dist = np.asarray(distance)
        inds = np.digitize(np_dist, np.array(self.bins))
        dataset.groups = labelList(inds)
        # np_groups = np.asarray(dataset.groups)
        # np_groups[:] = inds[:]
        # print("np_groups: ", np_groups)
        # print("dataset.groups: ", dataset.groups[1])
        return dataset
