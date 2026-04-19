Field Statistics
================

pyOFTools provides aggregators for computing statistics on fields. All aggregators handle parallel (MPI) reduction automatically.

Aggregators
-----------

Each aggregator takes a dataset and produces an ``AggregatedDataSet``:

.. list-table::
   :header-rows: 1

   * - Aggregator
     - What it computes
   * - ``Sum``
     - Sum of field values
   * - ``Mean``
     - Arithmetic mean
   * - ``Min``
     - Minimum value
   * - ``Max``
     - Maximum value
   * - ``VolIntegrate``
     - Sum weighted by cell volumes (volume integral)
   * - ``SurfIntegrate``
     - Sum weighted by face areas (surface integral)

Usage with the pipe operator:

.. code-block:: python

   from pyOFTools.builders import field
   from pyOFTools.aggregators import Sum, Mean, Min, Max, VolIntegrate

   @postProcess.Table("pressure_stats.csv")
   def pressure_stats(mesh):
       return field(mesh, "p") | Mean()

Binning
-------

The ``Directional`` node groups cells into spatial bins before aggregation. Bins are defined by edges along a direction vector:

.. code-block:: python

   from pyOFTools.binning import Directional

   @postProcess.Table("p_bins.csv")
   def pressure_bins(mesh):
       return (
           field(mesh, "p")
           | Directional(
               bins=[0.0, 0.1, 0.2, 0.3],
               direction=(1, 0, 0),
               origin=(0, 0, 0),
           )
           | Mean()
       )

This projects each cell centre onto the direction vector (relative to origin) and assigns it to a bin. The aggregator then computes per-bin results.

Spatial selectors
-----------------

Spatial selectors create masks that filter which cells are included in the computation:

.. code-block:: python

   from pyOFTools.spatial_selectors import Box, Sphere

   # Select cells inside a box
   box = Box(min=(0, 0, 0), max=(0.1, 0.1, 0.1))

   # Select cells inside a sphere
   sphere = Sphere(center=(0.5, 0.5, 0.5), radius=0.1)

   # Combine with boolean operators
   region = box & sphere       # intersection
   region = box | sphere       # union
   region = ~box               # complement

Spatial selectors are nodes --- use them in a pipeline before an aggregator:

.. code-block:: python

   @postProcess.Table("box_pressure.csv")
   def box_pressure(mesh):
       return (
           field(mesh, "p")
           | Box(min=(0, 0, 0), max=(0.1, 0.2, 0.01))
           | Mean()
       )
