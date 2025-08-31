from pybFoam import scalarField, vectorField, tensorField, fvMesh, volScalarField, volVectorField, volTensorField
import numpy as np
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional, Annotated, ClassVar
from .datasets import DataSets



class Node(BaseModel):
    type: Literal["node"] = "node"
    registry: ClassVar[list[any]] = []
    
    @classmethod
    def register(cls):
        def deco(subcls: any) -> any:
            cls.registry.append(subcls)
            return subcls
        return deco

    @classmethod
    def build_discriminated_union(cls):
        if not cls.registry:
            raise RuntimeError("No Node types registered.")
        union = Union[tuple(cls.registry)]
        return Annotated[union, Field(discriminator="type")]


    def compute(self, dataset: DataSets) -> DataSets:
        pass


