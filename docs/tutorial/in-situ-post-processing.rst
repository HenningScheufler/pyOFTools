In-Situ Post-Processing
=======================

This tutorial shows how to build a complete post-processing setup for a damBreak case with multiple outputs: volume tracking, mass distribution by spatial bins, and free surface area.

The decorator API
-----------------

``PostProcessorBase`` is the entry point. Each ``@Table`` decorator registers a computation that runs during the simulation:

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import field, iso_surface, residuals
   from pyOFTools.aggregators import VolIntegrate, Sum
   from pyOFTools.binning import Directional

   postProcess = PostProcessorBase()

The ``postProcess`` object collects all registered outputs. OpenFOAM calls ``postProcess(mesh)`` to create a runner, then calls ``.execute()`` / ``.write()`` / ``.end()`` at the appropriate times.

Volume integral
---------------

The simplest pipeline: read a field, integrate over the mesh volume.

.. code-block:: python

   @postProcess.Table("vol_alpha.csv")
   def vol_alpha(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

Output columns: ``time, alpha.water_volIntegrate``

Mass distribution with binning
------------------------------

The ``Directional`` node groups cells into spatial bins before aggregation. This computes mass in 5 bins along the x-direction:

.. code-block:: python

   @postProcess.Table("mass.csv")
   def mass_x(mesh):
       return (
           field(mesh, "rho")
           | Directional(
               bins=[0.0, 0.146, 0.292, 0.438, 0.584],
               direction=(1, 0, 0),
               origin=(0, 0, 0),
           )
           | VolIntegrate()
       )

Output columns: ``time, rho_volIntegrate, group``

Each row has a ``group`` index (0--4) corresponding to the bin.

To bin along a different direction, change ``direction``:

.. code-block:: python

   @postProcess.Table("mass_dist_height.csv")
   def mass_y(mesh):
       return (
           field(mesh, "rho")
           | Directional(
               bins=[0.0, 0.146, 0.292, 0.438, 0.584],
               direction=(0, 1, 0),
               origin=(0, 0, 0),
           )
           | VolIntegrate()
       )

Free surface area
-----------------

``iso_surface`` creates an iso-surface geometry. Piping it through ``area()`` populates the field with face area magnitudes, then ``Sum`` totals them:

.. code-block:: python

   @postProcess.Table("free_surface_area.csv")
   def free_surface_area(mesh):
       return iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()

Sampling a field onto a surface
-------------------------------

``sample(mesh, "p")`` interpolates a volume field onto the surface geometry:

.. code-block:: python

   @postProcess.Table("surface_pressure.csv")
   def surface_pressure(mesh):
       return iso_surface(mesh, "alpha.water", 0.5) | sample(mesh, "p") | Mean()

Solver residuals
----------------

``residuals`` extracts solver performance data (initial/final residuals, iteration count):

.. code-block:: python

   @postProcess.Table("residuals.csv")
   def solver_residuals(mesh):
       return residuals(mesh)

Output columns: ``time, residuals, field, solver, metric, iteration``

Write control
-------------

By default, ``@Table`` writes when OpenFOAM writes fields (``writeControl: writeTime``). To write every N timesteps:

.. code-block:: python

   @postProcess.Table("fast_output.csv", writeControl="timeStep", writeInterval=10)
   def frequent_output(mesh):
       return field(mesh, "p") | VolIntegrate()

controlDict setup
-----------------

The ``pyPostProcessing`` function object loads your Python file and calls the ``postProcess`` object:

.. code-block:: c

   functions
   {
       pyPostProcessing
       {
           libs            ("libembeddingPython.so");
           type            pyPostProcessing;
           writeControl    timeStep;
           writeInterval   1;
           pyFileName      postProcess;    // Python file name (without .py)
           pyClassName     postProcess;    // Python object name
       }
   }

``pyFileName`` is the module name (file without ``.py``). ``pyClassName`` is the name of the ``PostProcessorBase`` instance in that module.
