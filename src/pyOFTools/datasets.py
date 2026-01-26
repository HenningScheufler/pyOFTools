from __future__ import annotations

from typing import Optional, Union

from pybFoam import (
    boolList,
    labelList,
    scalarField,
    symmTensor,
    symmTensorField,
    tensor,
    tensorField,
    vector,
    vectorField,
    volScalarField,
    volSymmTensorField,
    volTensorField,
    volVectorField,
)
from pydantic import BaseModel

from .geometry import BoundaryMesh, InternalMesh, SetGeometry, SurfaceMesh

FieldType = Union[scalarField, vectorField, tensorField, symmTensorField]
GeoFieldType = Union[volScalarField, volVectorField, volTensorField, volSymmTensorField]

# Registry for Node subclasses
NODE_REGISTRY: dict[str, type] = {}


class InternalDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: InternalMesh
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None
    model_config = {"arbitrary_types_allowed": True}


class PatchDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: BoundaryMesh
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None

    model_config = {"arbitrary_types_allowed": True}


class SurfaceDataSet(BaseModel):
    name: str
    field: Optional[FieldType] = None
    geometry: SurfaceMesh
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None

    model_config = {"arbitrary_types_allowed": True}


class PointDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: SetGeometry
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None

    model_config = {"arbitrary_types_allowed": True}


SimpleType = Union[float, int, vector, tensor, symmTensor]


def _flatten_types(values: SimpleType) -> list[float]:
    out: list[float] = []
    if hasattr(values, "__len__"):
        out.extend([float(v) for v in values])  # type: ignore[union-attr]
    else:
        out.append(float(values))
    return out


def _value_columns(agg_dataset: "AggregatedDataSet") -> list[str]:
    out = []
    # check the each value in values.value as the same type
    value_types = {type(v.value) for v in agg_dataset.values}
    if len(value_types) > 1:
        raise ValueError("All values must be of the same type")

    if len(agg_dataset.values) == 0:
        raise ValueError("No values provided")

    _val = [v for v in agg_dataset.values]

    v0 = _val[0]
    if hasattr(v0.value, "__len__"):
        out.extend([f"{agg_dataset.name}_{j}" for j in range(len(v0.value))])
    else:
        out.append(agg_dataset.name)

    if _val[0].group_name:
        out.extend(_val[0].group_name)

    return out


class AggregatedData(BaseModel):
    value: SimpleType
    group: Optional[list[Union[int, str]]] = None
    group_name: Optional[list[str]] = None

    model_config = {"arbitrary_types_allowed": True}


class AggregatedDataSet(BaseModel):
    name: str
    values: list[AggregatedData]

    model_config = {"arbitrary_types_allowed": True}

    @property
    def headers(self) -> list[str]:
        headers = _value_columns(self)
        return headers

    @property
    def grouped_values(self) -> list[list[Union[float, int, str]]]:
        values_with_groups: list[list[Union[float, int, str]]] = []
        for value in self.values:
            row: list[Union[float, int, str]] = []
            row.extend(_flatten_types(value.value))
            # append group values if they exist
            if value.group:
                row.extend(value.group)
            values_with_groups.append(row)
        return values_with_groups


DataSets = Union[InternalDataSet, PatchDataSet, SurfaceDataSet, AggregatedDataSet]
