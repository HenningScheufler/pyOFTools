from typing import Union, Literal, Tuple, Annotated
from pydantic import BaseModel, Field
import numpy as np
import yaml

# --- Base class ---

class RegionSelector(BaseModel):
    type: str

    def compute(self, coords: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def __and__(self, other: 'RegionSelector') -> 'BinaryRegion':
        return BinaryRegion(type='binary', op='and', left=self, right=other)

    def __or__(self, other: 'RegionSelector') -> 'BinaryRegion':
        return BinaryRegion(type='binary', op='or', left=self, right=other)

    def __invert__(self) -> 'NotRegion':
        return NotRegion(type='not', region=self)

# --- Primitives ---

class Box(RegionSelector):
    type: Literal["box"]
    min: Tuple[float, float, float]
    max: Tuple[float, float, float]

    def compute(self, coords: np.ndarray) -> np.ndarray:
        return np.all((coords >= self.min) & (coords <= self.max), axis=1)

class Sphere(RegionSelector):
    type: Literal["sphere"]
    center: Tuple[float, float, float]
    radius: float

    def compute(self, coords: np.ndarray) -> np.ndarray:
        return np.linalg.norm(coords - self.center, axis=1) <= self.radius

# --- Logical ---

class NotRegion(RegionSelector):
    type: Literal["not"]
    region: 'RegionModel'

    def compute(self, coords: np.ndarray) -> np.ndarray:
        return ~self.region.compute(coords)

class BinaryRegion(RegionSelector):
    type: Literal["binary"]
    op: Literal["and", "or"]
    left: 'RegionModel'
    right: 'RegionModel'

    def compute(self, coords: np.ndarray) -> np.ndarray:
        l = self.left.compute(coords)
        r = self.right.compute(coords)
        return l & r if self.op == "and" else l | r

# --- Union of all region types ---

RegionModel = Annotated[
    Union[Box, Sphere, NotRegion, BinaryRegion],
    Field(discriminator='type')
]
NotRegion.model_rebuild()
BinaryRegion.model_rebuild()


def from_dict(data: dict) -> RegionModel:
    """Create a RegionModel from a dictionary using Pydantic's discriminated union."""
    from pydantic import TypeAdapter
    adapter = TypeAdapter(RegionModel)
    return adapter.validate_python(data)


def from_yaml(yaml_str: str) -> RegionModel:
    """Create a RegionModel from a YAML string."""
    data = yaml.safe_load(yaml_str)
    return from_dict(data)