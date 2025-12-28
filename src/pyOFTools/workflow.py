from pydantic import BaseModel, Field

from .datasets import DataSets
from .node import Node


def create_workflow() -> "WorkFlow":
    NodeUnion = Node.build_discriminated_union()

    class WorkFlow(BaseModel):
        initial_dataset: DataSets
        steps: list[NodeUnion] = Field(default_factory=list)

        def compute(self) -> DataSets:
            dataset = self.initial_dataset.model_copy()
            for step in self.steps:
                dataset = step.compute(dataset)
            return dataset

        model_config = {"arbitrary_types_allowed": True}

        def then(self, step: NodeUnion) -> "WorkFlow":
            self.steps.append(step)
            return self

    return WorkFlow


WorkFlow = create_workflow()
