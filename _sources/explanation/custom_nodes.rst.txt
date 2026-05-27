Custom nodes
============

Nodes are the building blocks of pyOFTools pipelines. You write a custom
node by subclassing ``BaseModel`` and registering it with
``@Node.register()``. The dataset types a node consumes and produces are
described in :doc:`datastructures`.

Creating a custom aggregator
----------------------------

A node receives a dataset and returns a (possibly different) dataset. An
aggregator returns an ``AggregatedDataSet`` summarising the input. Here is a
standard-deviation aggregator:

.. code-block:: python

   from typing import Literal, Optional
   from pydantic import BaseModel
   from pyOFTools.node import Node
   from pyOFTools.datasets import AggregatedData, AggregatedDataSet, DataSets
   from pyOFTools import aggregation

   @Node.register()
   class StdDev(BaseModel):
       type: Literal["stddev"] = "stddev"
       name: Optional[str] = None

       def compute(self, dataset: DataSets) -> AggregatedDataSet:
           mean_res = aggregation.mean(dataset.field, dataset.mask, dataset.groups)
           sum_sq_res = aggregation.sum(
               dataset.field, dataset.mask, dataset.groups,
               scalingFactor=dataset.field,  # field * field
           )
           # stddev = sqrt(E[x^2] - E[x]^2)
           # ... compute from mean_res and sum_sq_res ...

           return AggregatedDataSet(
               name=self.name or f"{dataset.name}_stddev",
               values=[AggregatedData(value=result)],
           )

Once registered, the node composes with the rest of the pipeline:

.. code-block:: python

   @postProcess.Table("p_stddev.csv")
   def pressure_stddev(mesh):
       return field(mesh, "p") | StdDev()

``aggregation.mean`` and ``aggregation.sum`` are MPI-aware: they call
``Foam::reduce`` internally, so your node works in parallel without any
extra code.

Creating a custom filter node
-----------------------------

A filter node transforms a dataset without aggregating. It returns the same
dataset type it received, usually with ``mask`` or ``groups`` populated:

.. code-block:: python

   @Node.register()
   class Threshold(BaseModel):
       type: Literal["threshold"] = "threshold"
       min_value: float = 0.0
       max_value: float = 1.0

       def compute(self, dataset: DataSets) -> DataSets:
           import numpy as np
           values = np.asarray(dataset.field)
           mask = (values >= self.min_value) & (values <= self.max_value)
           dataset.mask = mask
           return dataset

Nodes are composable because filters keep the dataset shape stable.
``Threshold`` produces an ``InternalDataSet`` with a mask; a downstream
``VolIntegrate`` honours that mask and integrates only the kept cells.

Node registration
-----------------

``@Node.register()`` adds the class to ``NODE_REGISTRY`` (see
:doc:`workflow_internals`), which is used to build a Pydantic discriminated
union. Two requirements:

- Each node must declare a unique ``type`` literal.
- Each node must implement ``compute(self, dataset) -> dataset``.

Registration makes your node behave identically to built-in nodes — it
works in ``| ...`` chains, round-trips through JSON, and picks up the same
validation errors when a dataset type mismatches.
