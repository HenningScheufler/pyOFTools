"""openfoam aggregation package"""

from typing import overload

import pybFoam.pybFoam_core


class scalarAggregationResult:
    @property
    def values(self) -> pybFoam.pybFoam_core.scalarField: ...

    @property
    def group(self) -> pybFoam.pybFoam_core.labelList | None: ...

class vectorAggregationResult:
    @property
    def values(self) -> pybFoam.pybFoam_core.vectorField: ...

    @property
    def group(self) -> pybFoam.pybFoam_core.labelList | None: ...

@overload
def sum(values: pybFoam.pybFoam_core.scalarField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None, *, scalingFactor: pybFoam.pybFoam_core.scalarField | None = None) -> scalarAggregationResult: ...

@overload
def sum(values: pybFoam.pybFoam_core.vectorField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None, *, scalingFactor: pybFoam.pybFoam_core.scalarField | None = None) -> vectorAggregationResult: ...

@overload
def mean(values: pybFoam.pybFoam_core.scalarField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None, *, scalingFactor: pybFoam.pybFoam_core.scalarField | None = None) -> scalarAggregationResult: ...

@overload
def mean(values: pybFoam.pybFoam_core.vectorField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None, *, scalingFactor: pybFoam.pybFoam_core.scalarField | None = None) -> vectorAggregationResult: ...

@overload
def max(values: pybFoam.pybFoam_core.scalarField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None) -> scalarAggregationResult: ...

@overload
def max(values: pybFoam.pybFoam_core.vectorField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None) -> vectorAggregationResult: ...

@overload
def min(values: pybFoam.pybFoam_core.scalarField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None) -> scalarAggregationResult: ...

@overload
def min(values: pybFoam.pybFoam_core.vectorField, mask: pybFoam.pybFoam_core.boolList | None = None, group: pybFoam.pybFoam_core.labelList | None = None) -> vectorAggregationResult: ...
