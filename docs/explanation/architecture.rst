Architecture
============

pyOFTools turns OpenFOAM simulation state into CSV tables in three moves:

1. **Wrap** — an ``fvMesh`` (or a sampled surface, or a sampled set) is
   wrapped in a geometry adapter and paired with a field to form a dataset.
2. **Transform** — the dataset flows through a chain of nodes (filters,
   binners, aggregators) via a ``WorkFlow``.
3. **Write** — a ``TableWriter`` runs the workflow once per OpenFOAM write
   interval and appends a row to a CSV.

That is the whole model. Everything else in this page elaborates on those
three pieces.

.. mermaid::

    graph LR
        subgraph "Step 1: Wrap"
            A["fvMesh + field name"]
            B["InternalDataSet"]
        end
        subgraph "Step 2: Transform"
            C["WorkFlow (chain of nodes)"]
        end
        subgraph "Step 3: Write"
            D["TableWriter"]
            E["postProcessing/*.csv"]
        end
        A --> B
        B --> C
        C --> D
        D --> E

For the shape of each dataset type and how they relate, see
:doc:`datastructures`. For what happens inside ``WorkFlow`` and
``TableWriter``, see :doc:`workflow_internals`.

Minimal example
---------------

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import field
   from pyOFTools.aggregators import VolIntegrate

   postProcess = PostProcessorBase()

   @postProcess.Table("volume.csv")
   def water_volume(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

This writes one CSV row per write interval, each with the volume integral of
``alpha.water``. The ``@Table`` decorator registers the function;
``PostProcessorBase.__call__(mesh)`` turns the registrations into
``TableWriter`` instances. The solver drives them through the OpenFOAM
function-object interface.

Why a pipeline?
---------------

A pipeline keeps each step small and orthogonal:

- **Spatial selectors** (``Box``, ``Sphere``) restrict *where*.
- **Binners** (``Directional``) restrict *how grouped*.
- **Aggregators** (``Sum``, ``Mean``, ``VolIntegrate``, ``SurfIntegrate``)
  restrict *what reduction*.

The same selectors and aggregators compose across datasets — a ``Box`` masks
volume cells, surface faces, and sampling points the same way — because the
middle stage speaks only in dataset types, not in OpenFOAM objects.

In-situ vs standalone
---------------------

pyOFTools is designed for **in-situ** execution: the pipeline runs inside a
live OpenFOAM solver, reading the current state at each write interval. The
``@PostProcessorBase`` / ``@Table`` API wires this to OpenFOAM's
function-object machinery via ``system/controlDict``
(see :doc:`/how-to/configure_controlDict`).

The same building blocks also work standalone: construct a ``WorkFlow``
directly from Python against a loaded case. The gallery scripts under
:doc:`/auto_tutorials/index` use the standalone path for testability.

Parallel execution
------------------

Under ``mpirun -np N``, ``TableWriter`` runs the workflow on every rank (so
MPI reductions inside the aggregator collect from all cells) and writes the
file on rank 0 only. You do not wire the reduction yourself; the aggregator
nodes already call ``Foam::reduce`` through pybFoam. The details are in
:doc:`workflow_internals`.
