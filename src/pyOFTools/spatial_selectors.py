from typing import Union, Literal, Tuple, Annotated
from pydantic import BaseModel, Field
from .datasets import DataSets
from .node import Node
import numpy as np
import yaml

# --- Base class ---

class SpatialSelector(Node):

    def compute(self, coords: DataSets) -> DataSets:
        raise NotImplementedError

    def __and__(self, other: 'SpatialSelector') -> 'BinarySpatialSelector':
        return BinarySpatialSelector(type='binary', op='and', left=self, right=other)

    def __or__(self, other: 'SpatialSelector') -> 'BinarySpatialSelector':
        return BinarySpatialSelector(type='binary', op='or', left=self, right=other)

    def __invert__(self) -> 'NotSpatialSelector':
        return NotSpatialSelector(type='not', region=self)

# --- Primitives ---
@Node.register()
class Box(SpatialSelector):
    type: Literal["box"]
    min: Tuple[float, float, float]
    max: Tuple[float, float, float]

    def compute(self, dataset: DataSets) -> DataSets:
        positions = np.asarray(dataset.geometry.positions)
        return np.all((positions >= self.min) & (positions <= self.max), axis=1)

@Node.register()
class Sphere(SpatialSelector):
    type: Literal["sphere"]
    center: Tuple[float, float, float]
    radius: float

    def compute(self, dataset: DataSets) -> DataSets:
        positions = np.asarray(dataset.geometry.positions)
        return np.linalg.norm(positions - self.center, axis=1) <= self.radius

# --- Logical ---
@Node.register()
class NotSpatialSelector(SpatialSelector):
    type: Literal["not"]
    region: 'SpatialSelectorModel'

    def compute(self, dataset: DataSets) -> DataSets:
        return ~self.region.compute(dataset)

@Node.register()
class BinarySpatialSelector(SpatialSelector):
    type: Literal["binary"]
    op: Literal["and", "or"]
    left: 'SpatialSelectorModel'
    right: 'SpatialSelectorModel'

    def compute(self, dataset: DataSets) -> DataSets:
        l = self.left.compute(dataset)
        r = self.right.compute(dataset)
        return l & r if self.op == "and" else l | r

SpatialSelectorModel = Annotated[
    Union[Box, Sphere, NotSpatialSelector, BinarySpatialSelector],
    Field(discriminator='type')
]
