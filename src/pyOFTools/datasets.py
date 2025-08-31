from pybFoam import (
    boolList,
    labelList,
    scalarField,
    vectorField,
    tensorField,
    fvMesh,
    volScalarField,
    volVectorField,
    volTensorField,
    vector,
    tensor,
)
import numpy as np
from pydantic import BaseModel, Field
from typing import Literal, Union, Optional, Annotated
from .geometry import InternalMesh, BoundaryMesh, SurfaceMesh

FieldType = Union[scalarField, vectorField, tensorField]
GeoFieldType = Union[volScalarField, volVectorField, volTensorField]

# Registry for Node subclasses
NODE_REGISTRY = {}


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
    field: FieldType
    geometry: SurfaceMesh
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None

    model_config = {"arbitrary_types_allowed": True}


SimpleType = Union[float, int, vector, tensor]


class AggregatedData(BaseModel):
    name: str
    value: SimpleType
    group_name: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class AggregatedDataSet(BaseModel):
    name: str
    values: list[AggregatedData]

    model_config = {"arbitrary_types_allowed": True}


DataSets = Union[InternalDataSet, PatchDataSet, SurfaceDataSet, AggregatedDataSet]
