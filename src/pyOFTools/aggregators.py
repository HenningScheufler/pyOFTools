from typing import Literal, Optional
from pydantic import BaseModel, Field
import pybFoam
from pybFoam import aggregation
from .datasets import DataSets, AggregatedDataSet, AggregatedData
from .node import Node


@Node.register()
class Sum(BaseModel):
    type: Literal["sum"] = "sum"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        agg_res = aggregation.sum(dataset.field, dataset.mask, dataset.groups)

        agg_data = []
        for i, val in enumerate(agg_res.values):
            agg_data.append(
                AggregatedData(
                    name=f"{dataset.name}_sum_{i}",
                    value=val,
                    group_name=agg_res.group[i] if agg_res.group else None,
                )
            )

        return AggregatedDataSet(
            name=f"{self.name or 'sum'}",
            values=agg_data,
        )


@Node.register()
class Mean(BaseModel):
    type: Literal["mean"] = "mean"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        res_mean = aggregation.mean(dataset.field)
        result = AggregatedDataSet(
            name=f"{self.name or 'mean'}",
            values=[AggregatedData(name=f"{dataset.name}_mean", value=res_mean)],
        )
        return result


@Node.register()
class Max(BaseModel):
    type: Literal["max"] = "max"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> any:
        results = pybFoam.max(dataset.field)
        return results
