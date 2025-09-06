from typing import Literal, Optional, Union
from pydantic import BaseModel, Field
import pybFoam
from pybFoam import aggregation
from .datasets import DataSets, AggregatedDataSet, AggregatedData
from .node import Node

def _compute_agg_data(
    agg_res: Union[aggregation.scalarAggregationResult, aggregation.vectorAggregationResult],
) -> list[AggregatedData]:
    agg_data = []
    group = list(agg_res.group) if agg_res.group else None
    group_names = None
    if group:
        group_names = ["group"]
    for i, val in enumerate(agg_res.values):
        agg_data.append(
            AggregatedData(
                value=val,
                group=[group[i]] if group else None,
                group_name=group_names if group_names else None,
            )
        )

    return agg_data

@Node.register()
class Sum(BaseModel):
    type: Literal["sum"] = "sum"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        agg_res = aggregation.sum(dataset.field, dataset.mask, dataset.groups)

        agg_data = _compute_agg_data(agg_res)

        return AggregatedDataSet(
            name=f'{self.name or f"{dataset.name}_sum"}',
            values=agg_data,
        )


@Node.register()
class Mean(BaseModel):
    type: Literal["mean"] = "mean"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        res_mean = aggregation.mean(dataset.field)
        result = AggregatedDataSet(
            name=f'{self.name or f"{dataset.name}_mean"}',
            values=[AggregatedData(name=f"{dataset.name}_mean", value=res_mean)],
        )
        return result


@Node.register()
class Max(BaseModel):
    type: Literal["max"] = "max"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> any:
        agg_res = aggregation.max(dataset.field, dataset.mask, dataset.groups)

        agg_data = _compute_agg_data(agg_res)

        return AggregatedDataSet(
            name=f"{self.name or f'{dataset.name}_max'}",
            values=agg_data,
        )

@Node.register()
class Min(BaseModel):
    type: Literal["min"] = "min"
    name: Optional[str] = None

    def compute(self, dataset: DataSets) -> AggregatedDataSet:
        agg_res = aggregation.min(dataset.field, dataset.mask, dataset.groups)

        agg_data = _compute_agg_data(agg_res)

        return AggregatedDataSet(
            name=f"{self.name or f'{dataset.name}_min'}",
            values=agg_data,
        )
