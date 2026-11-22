Core data structures
====================

pyOFTools moves data through a pipeline. Every stage has a concrete Python
type, and every type has a small, well-defined shape. This page lists them
and shows how they connect.

Knowing these types is optional for writing a post-processor — the
``builders`` module hides most of them — but it is essential for writing
custom nodes, reading tracebacks, or debugging why an aggregator rejected a
dataset.

The pipeline in one picture
---------------------------

.. mermaid::

    graph LR
        subgraph Source
            Mesh["fvMesh / sampledSurface / sampledSet"]
        end
        subgraph "Geometry adapter"
            Adapter["InternalMesh<br/>SurfaceMesh<br/>SetGeometry<br/>BoundaryMesh"]
        end
        subgraph "Dataset (field + geometry + mask/groups)"
            DS["InternalDataSet<br/>SurfaceDataSet<br/>PointDataSet<br/>PatchDataSet"]
        end
        subgraph "Nodes"
            Filter["Filter node<br/>(Box, Sphere, Threshold)"]
            Binner["Binner<br/>(Directional)"]
            Agg["Aggregator<br/>(Sum, Mean, VolIntegrate)"]
        end
        Result["AggregatedDataSet"]
        Writer["TableWriter → CSV"]

        Mesh --> Adapter
        Adapter --> DS
        DS -->|masked| Filter
        Filter --> DS
        DS -->|grouped| Binner
        Binner --> DS
        DS --> Agg
        Agg --> Result
        Result --> Writer

Read the arrows as "produces". The dataset types in the middle are the
stable currency of the pipeline: filters and binners return a dataset of the
same kind they received, aggregators always return an ``AggregatedDataSet``.

The four input datasets
-----------------------

All four share the same outer shape — ``name``, ``field``, ``geometry``,
optional ``mask``, optional ``groups`` — and differ only in the geometry they
carry. Pydantic ``BaseModel`` is used so nodes can declare dataset fields by
type and have them validated at construction.

.. list-table::
   :header-rows: 1
   :widths: 20 24 30 26

   * - Dataset
     - Geometry protocol
     - What the geometry carries
     - Produced by
   * - ``InternalDataSet``
     - ``InternalMesh``
     - ``positions`` (cell centres), ``volumes``
     - ``field(mesh, name)``
   * - ``SurfaceDataSet``
     - ``SurfaceMesh``
     - ``positions`` (face centres), ``face_areas``, ``face_area_magnitudes``, ``total_area``
     - ``create_plane``, ``create_iso_surface``, ``create_patch_surface``
   * - ``PointDataSet``
     - ``SetGeometry``
     - ``positions`` (sample points), ``distance`` (cumulative arc length)
     - ``create_uniform_set``, ``create_polyline_set``, ``create_circle_set``, ``create_cloud_set``
   * - ``PatchDataSet``
     - ``BoundaryMesh``
     - ``positions`` (patch face centres)
     - Boundary-field builders

``field`` is a pybFoam ``scalarField`` / ``vectorField`` / ``tensorField`` /
``symmTensorField``. Size matches the geometry (one entry per cell, face, or
sample point).

``mask`` is an optional boolean array selecting which elements participate in
subsequent steps. ``Box`` and ``Sphere`` write to it; aggregators honour it.

``groups`` is an optional integer array assigning each element to a bin.
``Directional`` writes to it; aggregators reduce per-group, producing one
``AggregatedData`` row per group.

The geometry protocols
----------------------

Geometry is a Python ``Protocol``, not a class hierarchy. Anything with the
right attributes satisfies it, so OpenFOAM objects wrap into the pipeline via
thin adapters (pure Python, no copies):

- ``FvMeshInternalAdapter(mesh)`` — exposes cell centres and cell volumes
  from an ``fvMesh``.
- ``SampledSurfaceAdapter(surface)`` — exposes face centres and face areas
  from a ``sampledSurface`` (what ``create_plane`` and ``create_iso_surface``
  return underneath).
- ``SampledSetAdapter(set)`` — exposes point positions and distances from a
  ``sampledSet`` (underneath the ``create_*_set`` builders).

Once wrapped, nothing in the pipeline knows it is talking to an OpenFOAM
object — only to an ``InternalMesh``, ``SurfaceMesh``, etc. This is what lets
the same ``Mean`` node operate on volumes, surfaces, or lines.

The output dataset
------------------

``AggregatedDataSet`` is the pipeline's exit type. It has no geometry and no
mask — just a name and a list of ``AggregatedData`` rows. Each row carries:

- ``value`` — a scalar, vector, or tensor result.
- ``group`` — the bin label(s) the value belongs to (``None`` if ungrouped).
- ``group_name`` — the names of the grouping columns.

``AggregatedDataSet.headers`` and ``AggregatedDataSet.grouped_values`` expose
the data in a CSV-ready shape; ``TableWriter`` consumes those directly.

Which node consumes which dataset
---------------------------------

Most nodes are geometry-agnostic: ``Sum`` and ``Mean`` work on any dataset
because they only touch ``field``, ``mask``, and ``groups``. A few need
specific geometry:

- ``VolIntegrate`` requires ``InternalMesh`` (needs cell volumes).
- ``SurfIntegrate`` requires ``SurfaceMesh`` or ``BoundaryMesh`` (needs face
  areas).
- ``Directional`` reads ``positions`` from any geometry, so it works on all
  four input dataset types.
- ``Box`` and ``Sphere`` read ``positions`` and write to ``mask``; they also
  work on all four.

A type mismatch surfaces as a Pydantic validation error at node construction
or a ``TypeError`` at ``compute()`` time, not as silent wrong results.

Lifetime and ownership
----------------------

- A ``WorkFlow`` is rebuilt every time step inside
  :class:`~pyOFTools.tables.table.TableWriter`. The field data is read fresh
  from the running solver, so you see current values — not a stale snapshot.
- Geometry adapters hold references to the underlying OpenFOAM objects.
  Those live for the lifetime of the ``fvMesh``. Don't cache an adapter past
  a mesh motion / topology change.
- Aggregation results (the ``AggregatedDataSet``) are plain Python numbers
  and lists. They are safe to pickle, compare in tests, or return from a
  function.

See also
--------

- :doc:`workflow_internals` — how ``WorkFlow`` chains nodes and what
  ``TableWriter`` does in parallel.
- :doc:`custom_nodes` — the ``compute(dataset) -> dataset`` contract you
  implement when you add a new node.
