import numpy as np
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional, Annotated, ClassVar
from .datasets import DataSets
from .node import Node


class CSVWriter(BaseModel):
    name: str
    header: list[str]

    def create_file(self):
        with open(f"{self.name}.csv", "w") as f:
            f.write(",".join(self.header) + "\n")

    def write_data(self, time: float, values: list[float]):
        with open(f"{self.name}.csv", "a") as f:
            f.write(",".join(map(str, [time] + values)) + "\n")

    def close(self):
        pass
