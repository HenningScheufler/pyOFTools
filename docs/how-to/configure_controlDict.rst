Wire pyOFTools into ``system/controlDict``
==========================================

This recipe shows how to attach a ``PostProcessorBase`` subclass as an
OpenFOAM function object so it runs every write interval during the solver
loop. Use this when you have a working post-processor (see
:doc:`/auto_tutorials/example_01_hello_pyoftools`) and want to execute it
in-situ.

Prerequisites
-------------

- OpenFOAM is sourced and pybFoam is installed.
- A running case directory with ``system/controlDict``, ``constant/``,
  ``0.orig/``.
- ``libembeddingPython.so`` is available — this is what lets OpenFOAM load
  a Python function object (ships with pybFoam-based builds).

Recipe
------

1. **Write the post-processor.** Save as ``postProcess.py`` in the case root
   (next to ``system/``):

   .. code-block:: python

      from pyOFTools.postprocessor import PostProcessorBase
      from pyOFTools.builders import field, iso_surface, residuals
      from pyOFTools.aggregators import VolIntegrate, Sum

      postProcess = PostProcessorBase()

      @postProcess.Table("vol_alpha.csv")
      def vol_alpha(mesh):
          return field(mesh, "alpha.water") | VolIntegrate()

      @postProcess.Table("free_surface_area.csv")
      def free_surface_area(mesh):
          return iso_surface(mesh, "alpha.water", 0.5) | Sum()

      @postProcess.Table("residuals.csv")
      def solver_residuals(mesh):
          return residuals(mesh)

   The module-level instance must be called ``postProcess`` if you use the
   default ``pyClassName`` below — otherwise change the class name to match.

2. **Register the function object** in ``system/controlDict``:

   .. code-block:: c

      functions
      {
          pyPostProcessing
          {
              libs            ("libembeddingPython.so");
              type            pyPostProcessing;
              writeControl    timeStep;
              writeInterval   1;
              pyFileName      postProcess;   // postProcess.py
              pyClassName     postProcess;   // module-level instance name
          }
      }

   - ``pyFileName`` is the Python module (no ``.py`` extension).
   - ``pyClassName`` is the *name of the ``PostProcessorBase`` instance* in
     that module, not a class. The embedding loader looks up
     ``postProcess.postProcess`` in this example.

3. **Run the solver** from the case directory:

   .. code-block:: bash

      blockMesh
      setFields       # if the case needs it
      interFoam      # or your solver

4. **Read the output** from ``postProcessing/``:

   .. code-block:: text

      postProcessing/
      ├── vol_alpha.csv
      ├── free_surface_area.csv
      └── residuals.csv

   Each file has a ``time`` column and one column per aggregated value.

Parallel runs
-------------

Run as usual:

.. code-block:: bash

   decomposePar
   mpirun -np 4 interFoam -parallel

``TableWriter`` runs the workflow on every rank (so internal ``Foam::reduce``
calls see all cells) but only writes on rank 0, so you get one CSV per
output file — not one per processor.

Picking ``writeControl``
------------------------

- ``timeStep`` + ``writeInterval 1`` — write every step. Highest cost, best
  time resolution. Good for statistics.
- ``writeTime`` — write only when the solver writes fields. Cheapest, same
  cadence as the fields on disk.
- ``adjustableRunTime`` + ``writeInterval 0.05`` — fixed wall-clock cadence,
  useful when ``adjustTimeStep yes``.

See also
--------

- :doc:`troubleshooting` — ``pyFileName``/``pyClassName`` mistakes, CSV
  files not appearing, SIGFPE on numpy import.
- :doc:`migrate_to_postprocessor_api` — porting a pre-decorator
  post-processor to this pattern.
- :doc:`/explanation/architecture` — what ``@Table`` actually registers and
  how ``PostProcessorBase`` becomes a function object.
