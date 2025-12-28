from typing import Literal, Tuple

import numpy as np
from pybFoam import labelList, mag, vector

from .datasets import DataSets
from .node import Node


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
        return dataset
