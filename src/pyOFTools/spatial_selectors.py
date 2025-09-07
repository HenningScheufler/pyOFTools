from pybFoam import boolList
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

    def __and__(self, other: "SpatialSelector") -> "BinarySpatialSelector":
        return BinarySpatialSelector(type="binary", op="and", left=self, right=other)

    def __or__(self, other: "SpatialSelector") -> "BinarySpatialSelector":
        return BinarySpatialSelector(type="binary", op="or", left=self, right=other)

    def __invert__(self) -> "NotSpatialSelector":
        return NotSpatialSelector(type="not", region=self)


# --- Primitives ---
@Node.register()
class Box(SpatialSelector):
    type: Literal["box"] = "box"
    min: Tuple[float, float, float]
    max: Tuple[float, float, float]

    def compute(self, dataset: DataSets) -> DataSets:
        positions = np.asarray(dataset.geometry.positions)
        mask = np.all((positions >= self.min) & (positions <= self.max), axis=1)
        dataset.mask = boolList(mask)
        return dataset


@Node.register()
class Sphere(SpatialSelector):
    type: Literal["sphere"] = "sphere"
    center: Tuple[float, float, float]
    radius: float

    def compute(self, dataset: DataSets) -> DataSets:
        positions = np.asarray(dataset.geometry.positions)
        mask = np.linalg.norm(positions - self.center, axis=1) <= self.radius
        dataset.mask = boolList(mask)
        return dataset


# --- Logical ---
@Node.register()
class NotSpatialSelector(SpatialSelector):
    type: Literal["not"]
    region: "SpatialSelectorModel"

    def compute(self, dataset: DataSets) -> DataSets:
        dataset.mask = ~np.asarray(self.region.compute(dataset).mask)
        return dataset


@Node.register()
class BinarySpatialSelector(SpatialSelector):
    type: Literal["binary"]
    op: Literal["and", "or"]
    left: "SpatialSelectorModel"
    right: "SpatialSelectorModel"

    def compute(self, dataset: DataSets) -> DataSets:
        ds_l = self.left.compute(dataset)
        ds_r = self.right.compute(dataset)
        mask = (
            np.asarray(ds_l.mask) & np.asarray(ds_r.mask)
            if self.op == "and"
            else np.asarray(ds_l.mask) | np.asarray(ds_r.mask)
        )
        dataset.mask = boolList(mask)
        return dataset


SpatialSelectorModel = Annotated[
    Union[Box, Sphere, NotSpatialSelector, BinarySpatialSelector],
    Field(discriminator="type"),
]
