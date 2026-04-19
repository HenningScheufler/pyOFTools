Custom Nodes
============

Nodes are the building blocks of pyOFTools pipelines. You can create custom nodes by subclassing ``BaseModel`` and registering them with ``@Node.register()``.

Creating a custom aggregator
-----------------------------

A node receives a dataset and returns a (possibly different) dataset. Here's a custom aggregator that computes the standard deviation:

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

Once registered, the node works in pipelines:

.. code-block:: python

   @postProcess.Table("p_stddev.csv")
   def pressure_stddev(mesh):
       return field(mesh, "p") | StdDev()

Creating a custom filter node
-----------------------------

Filter nodes transform datasets without aggregating. They receive and return the same dataset type:

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

Node registration
-----------------

``@Node.register()`` adds the class to a global registry. This registry is used to build a Pydantic discriminated union, enabling serialization and deserialization of pipelines. Each node must have a unique ``type`` literal.
