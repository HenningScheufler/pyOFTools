WorkFlow internals
==================

This page documents what ``WorkFlow``, ``PostProcessorBase``, and
``TableWriter`` do under the hood. You only need this if you are extending
the library or debugging a tricky pipeline.

The dataset types referenced below are described in :doc:`datastructures`.

The builder layer
-----------------

``field()``, ``iso_surface()``, and ``residuals()`` in
:mod:`pyOFTools.builders` are convenience wrappers that construct a
``WorkFlow`` seeded with the right initial dataset:

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

Prefer the builder API. Reach for the manual construction only when you need
a dataset type no builder covers.

WorkFlow execution
------------------

``WorkFlow`` is a Pydantic model carrying an initial dataset and an ordered
list of nodes:

.. code-block:: python

   workflow = WorkFlow(initial_dataset=dataset)
   workflow = workflow.then(Directional(...))   # returns new WorkFlow
   workflow = workflow.then(VolIntegrate())     # returns new WorkFlow
   result = workflow.compute()                  # runs every node

``.then(node)`` returns a *new* ``WorkFlow`` — nothing is mutated in place,
so a pipeline can be passed around or reused safely. The ``|`` operator is
syntactic sugar for ``.then``.

``compute()`` runs each node's ``compute(dataset) -> dataset`` method in
order, threading the output of one into the input of the next. Filters and
binners return a dataset of the same kind (just with ``mask`` or ``groups``
populated); aggregators return an ``AggregatedDataSet``. The final return
value is whatever the last node returned — usually the
``AggregatedDataSet``.

PostProcessorBase and TableWriter
---------------------------------

``PostProcessorBase`` collects ``@Table`` decorated functions and, when
invoked with a mesh, produces a ``PostProcessorRunner`` that owns one
``TableWriter`` per decorated function:

.. code-block:: text

   PostProcessorBase
     ├── @Table("file1.csv") → func1
     ├── @Table("file2.csv") → func2
     └── __call__(mesh) → PostProcessorRunner
                            ├── TableWriter(func1, "file1.csv")
                            └── TableWriter(func2, "file2.csv")

``TableWriter`` dispatches to a format-specific writer (``CSVWriter``,
``DATWriter``) based on file extension and implements the OpenFOAM
function-object interface (``execute``, ``write``, ``end``). OpenFOAM drives
these methods from the solver loop; on each write interval, the writer:

1. Calls the user function with the current ``mesh`` to get a fresh
   ``WorkFlow``.
2. Runs ``workflow.compute()`` to produce an ``AggregatedDataSet``.
3. Appends a row (or per-bin rows) to the output file.

In parallel (``mpirun -np N``) the workflow runs on **every** rank so the
aggregator nodes' internal ``Foam::reduce`` calls collect data from all
cells; only rank 0 writes the file. You do not invoke ``Foam::reduce``
yourself — the aggregator does it.

Node lookup and serialization
-----------------------------

Nodes are registered with ``@Node.register()``, which adds them to a global
``NODE_REGISTRY`` used to build a Pydantic discriminated union. This is what
lets a ``WorkFlow`` round-trip to JSON (for example, to log the exact
pipeline that produced a CSV) and lets custom nodes participate on equal
footing with built-in ones. See :doc:`custom_nodes` for the registration
pattern.
