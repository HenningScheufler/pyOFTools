Workflow Internals
==================

This page documents the internal architecture of pyOFTools. You only need this if you are extending the library or building custom integrations.

The builder layer
-----------------

The ``field()``, ``iso_surface()``, and ``residuals()`` functions in ``pyOFTools.builders`` are convenience wrappers that construct a ``WorkFlow`` with the appropriate initial dataset:

.. code-block:: python

   from pyOFTools.builders import field

   # This:
   workflow = field(mesh, "alpha.water") | VolIntegrate()

   # Is equivalent to:
   from pybFoam import volScalarField
   from pyOFTools.datasets import InternalDataSet
   from pyOFTools.geometry import FvMeshInternalAdapter
   from pyOFTools.workflow import WorkFlow

   alpha = volScalarField.read_field(mesh, "alpha.water")
   dataset = InternalDataSet(
       name="alpha.water",
       field=alpha.internalField(),
       geometry=FvMeshInternalAdapter(mesh),
   )
   workflow = WorkFlow(initial_dataset=dataset).then(VolIntegrate())

The builder API is the recommended way to create workflows. Use the manual approach only when you need a dataset type that builders don't support.

Dataset types
-------------

.. list-table::
   :header-rows: 1

   * - Type
     - Geometry
     - Use case
   * - ``InternalDataSet``
     - Cell centres + volumes
     - Volume fields (from ``field()``)
   * - ``SurfaceDataSet``
     - Face centres + face areas
     - Sampled surfaces, iso-surfaces
   * - ``PointDataSet``
     - Point positions + distances
     - Line/set sampling
   * - ``PatchDataSet``
     - Patch face centres
     - Boundary data
   * - ``AggregatedDataSet``
     - None (scalar results)
     - Output of aggregators

All dataset types carry optional ``mask`` (boolean array) and ``groups`` (label array) fields that control which elements participate in aggregation and how they are grouped.

Geometry adapters
-----------------

Geometry adapters wrap OpenFOAM objects to satisfy the geometry protocols:

- ``FvMeshInternalAdapter(mesh)`` --- wraps ``fvMesh`` for cell centres and volumes
- ``SampledSurfaceAdapter(surface)`` --- wraps ``sampledSurface`` for face geometry
- ``SampledSetAdapter(set)`` --- wraps ``sampledSet`` for point positions and distances

WorkFlow execution
------------------

``WorkFlow`` is a Pydantic model that chains an initial dataset through a list of nodes:

.. code-block:: python

   workflow = WorkFlow(initial_dataset=dataset)
   workflow = workflow.then(Directional(...))   # returns new WorkFlow
   workflow = workflow.then(VolIntegrate())      # returns new WorkFlow
   result = workflow.compute()                   # executes all steps

The ``|`` operator is syntactic sugar for ``.then()``.

``compute()`` executes each node in sequence, passing the output of one as the input to the next. The final result is typically an ``AggregatedDataSet``.

TableWriter and PostProcessorBase
----------------------------------

``PostProcessorBase`` collects ``@Table`` decorated functions and creates ``TableWriter`` instances when called with a mesh:

.. code-block:: text

   PostProcessorBase
     ├── @Table("file1.csv") → func1
     ├── @Table("file2.csv") → func2
     └── __call__(mesh) → PostProcessorRunner
                            ├── TableWriter(func1, "file1.csv")
                            └── TableWriter(func2, "file2.csv")

``TableWriter`` dispatches to format-specific writers (``CSVWriter``, ``DATWriter``) based on file extension. It implements the OpenFOAM function object interface (``execute``, ``write``, ``end``).

In parallel, ``TableWriter`` calls the workflow on all ranks (so ``Foam::reduce()`` works) but only writes the file on the master rank.
