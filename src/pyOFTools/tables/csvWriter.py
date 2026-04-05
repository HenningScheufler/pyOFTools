from __future__ import annotations

import os
from typing import Any, Optional

from pydantic import BaseModel

from ..datasets import DataSets


def _flatten(values: Any) -> list[Any]:
    out: list[Any] = []
    for v in values:
        if hasattr(v, "__len__"):
            out.extend(list(v))
        else:
            out.append(v)
    return out


def _add_indices(values: Any) -> list[str]:
    out: list[str] = []
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

    def create_file(self) -> None:
        # create parent folder if it does not exists and parent folder is not ''
        if os.path.dirname(self.file_path) and not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as f:
            if self.header:
                f.write(",".join(self.header) + "\n")

    def _write_header(self, dataset: DataSets) -> None:
        if self.header is None:
            self.header = ["time"] + dataset.headers  # type: ignore[union-attr]
            with open(self.file_path, "w") as f:
                f.write(",".join(self.header) + "\n")

    def write_result(self, time: float, result: DataSets) -> None:
        """Write pre-computed result to CSV (no workflow.compute() call)."""
        if self.header is None:
            self._write_header(result)

        with open(self.file_path, "a") as f:
            for val in result.grouped_values:  # type: ignore[union-attr]
                f.write(",".join(map(str, [time] + val)) + "\n")

    def close(self) -> None:
        pass
