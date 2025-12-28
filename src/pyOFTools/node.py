from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Union

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .datasets import DataSets


class Node(BaseModel):
    type: str = "node"
    registry: ClassVar[list[type]] = []  # type: ignore[valid-type]

    @classmethod
    def register(cls) -> Any:
        def deco(subcls: type) -> type:
            cls.registry.append(subcls)
            return subcls

        return deco

    @classmethod
    def build_discriminated_union(cls) -> Any:
        if not cls.registry:
            raise RuntimeError("No Node types registered.")
        union = Union[tuple(cls.registry)]  # type: ignore[valid-type]
        return Annotated[union, Field(discriminator="type")]

    def compute(self, dataset: "DataSets") -> "DataSets":
        raise NotImplementedError("Subclasses must implement compute method")
