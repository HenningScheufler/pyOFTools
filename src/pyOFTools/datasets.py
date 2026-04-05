from __future__ import annotations

from typing import Annotated, Optional, Union

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
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema

from .geometry import BoundaryMesh, InternalMesh, SetGeometry, SurfaceMesh


def _make_instance_schema(cls):  # type: ignore[no-untyped-def]
    """Build a Pydantic core schema that does an isinstance check."""

    def _validate(v):  # type: ignore[no-untyped-def]
        if isinstance(v, cls):
            return v
        raise ValueError(f"Expected {cls.__name__}, got {type(v)}")

    return core_schema.no_info_plain_validator_function(
        _validate,
        serialization=core_schema.to_string_ser_schema(),
    )


class _PydanticWrapper:
    """Attach a working __get_pydantic_core_schema__ to any C++ type."""

    def __init__(self, tp: type) -> None:
        self.tp = tp

    def __get_pydantic_core_schema__(
        self, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return _make_instance_schema(self.tp)


# Wrapped field types
PydanticScalarField = Annotated[scalarField, _PydanticWrapper(scalarField)]
PydanticVectorField = Annotated[vectorField, _PydanticWrapper(vectorField)]
PydanticTensorField = Annotated[tensorField, _PydanticWrapper(tensorField)]
PydanticSymmTensorField = Annotated[symmTensorField, _PydanticWrapper(symmTensorField)]

# Wrapped geo field types
PydanticVolScalarField = Annotated[volScalarField, _PydanticWrapper(volScalarField)]
PydanticVolVectorField = Annotated[volVectorField, _PydanticWrapper(volVectorField)]
PydanticVolTensorField = Annotated[volTensorField, _PydanticWrapper(volTensorField)]
PydanticVolSymmTensorField = Annotated[volSymmTensorField, _PydanticWrapper(volSymmTensorField)]

# Wrapped primitive types
PydanticBoolList = Annotated[boolList, _PydanticWrapper(boolList)]
PydanticLabelList = Annotated[labelList, _PydanticWrapper(labelList)]
PydanticVector = Annotated[vector, _PydanticWrapper(vector)]
PydanticTensor = Annotated[tensor, _PydanticWrapper(tensor)]
PydanticSymmTensor = Annotated[symmTensor, _PydanticWrapper(symmTensor)]

# Type aliases used throughout pyOFTools
FieldType = Union[
    PydanticScalarField, PydanticVectorField, PydanticTensorField, PydanticSymmTensorField
]
GeoFieldType = Union[
    PydanticVolScalarField, PydanticVolVectorField, PydanticVolTensorField, PydanticVolSymmTensorField
]
SimpleType = Union[float, int, PydanticVector, PydanticTensor, PydanticSymmTensor]



# Registry for Node subclasses
NODE_REGISTRY: dict[str, type] = {}


class InternalDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: InternalMesh
    mask: Optional[PydanticBoolList] = None
    groups: Optional[PydanticLabelList] = None
    model_config = {"arbitrary_types_allowed": True}


class PatchDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: BoundaryMesh
    mask: Optional[PydanticBoolList] = None
    groups: Optional[PydanticLabelList] = None

    model_config = {"arbitrary_types_allowed": True}


class SurfaceDataSet(BaseModel):
    name: str
    field: Optional[FieldType] = None
    geometry: SurfaceMesh
    mask: Optional[PydanticBoolList] = None
    groups: Optional[PydanticLabelList] = None

    model_config = {"arbitrary_types_allowed": True}


class PointDataSet(BaseModel):
    name: str
    field: FieldType
    geometry: SetGeometry
    mask: Optional[PydanticBoolList] = None
    groups: Optional[PydanticLabelList] = None

    model_config = {"arbitrary_types_allowed": True}


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


DataSets = Union[InternalDataSet, PatchDataSet, SurfaceDataSet, PointDataSet, AggregatedDataSet]
