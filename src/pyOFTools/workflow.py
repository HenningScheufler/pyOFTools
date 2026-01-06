from pydantic import BaseModel, Field

from .datasets import DataSets
from .node import Node


def create_workflow() -> "WorkFlow":  # type: ignore[valid-type]
    NodeUnion = Node.build_discriminated_union()

    class WorkFlow(BaseModel):
        initial_dataset: DataSets
        steps: list[NodeUnion] = Field(default_factory=list)  # type: ignore[valid-type]

        def compute(self) -> DataSets:
            dataset = self.initial_dataset.model_copy()
            for step in self.steps:
                dataset = step.compute(dataset)  # type: ignore[attr-defined]
            return dataset

        model_config = {"arbitrary_types_allowed": True}

        def then(self, step: NodeUnion) -> "WorkFlow":  # type: ignore[valid-type]
            self.steps.append(step)
            return self

        def __or__(self, step: NodeUnion) -> "WorkFlow":  # type: ignore[valid-type]
            """Support pipe operator: workflow | aggregator"""
            return self.then(step)

    return WorkFlow


WorkFlow = create_workflow()
