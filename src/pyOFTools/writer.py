import numpy as np
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional, Annotated, ClassVar, Iterable
from .datasets import DataSets
from pybFoam import vector, tensor, symmTensor
from .node import Node

# include for type checking only to avoid circular import

# from .workflow import Workflow


def _flatten(values):
    out = []
    for v in values:
        if hasattr(v, "__len__"):
            out.extend(list(v))
        else:
            out.append(v)
    return out


def _add_indices(values):
    out = []
    for v in values:
        # If v has a length and is not a string/bytes, treat as vector-like
        if hasattr(v.value, "__len__"):
            out.extend([f"{v.name}_{j}" for j in range(len(v.value))])
        else:
            out.append(v.name if hasattr(v, "name") else str(v))
    return out


class CSVWriter(BaseModel):
    file_path: str
    header: Optional[list[str]] = None

    def create_file(self):
        with open(self.file_path, "w") as f:
            if self.header:
                f.write(",".join(self.header) + "\n")

    def _write_header(self, dataset: DataSets):
        if self.header is None:
            self.header = ["time"] + dataset.headers
            with open(self.file_path, "w") as f:
                f.write(",".join(self.header) + "\n")

    def write_data(self, time: float, workflow: "WorkFlow") -> None:
        res: DataSets = workflow.compute()
        if self.header is None:
            self._write_header(res)

        with open(self.file_path, "a") as f:
            for val in res.grouped_values:
                f.write(",".join(map(str, [time] + val)) + "\n")

    def close(self):
        pass
