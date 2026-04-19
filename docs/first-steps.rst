First Steps
===========

This example adds Python post-processing to an OpenFOAM case. After following these steps, your solver will write CSV files with field statistics at every timestep.

How it works
------------

pyOFTools follows a pipeline pattern: data flows from OpenFOAM fields through processing nodes into output files.

.. mermaid::

   graph LR
       subgraph "Builders"
           field["field(mesh, name)"]
           iso["iso_surface(mesh, name, val)"]
           line_b["line(mesh, name, start, end, n, field)"]
       end
       subgraph "Nodes"
           Directional
           Box
           Sphere
       end
       subgraph "Aggregators"
           VolIntegrate
           Sum
           Mean
           Min
           Max
       end
       subgraph "Output"
           Table["@Table → CSV"]
       end

       field --> |"pipe &#124;"| Directional
       field --> |"pipe &#124;"| VolIntegrate
       iso --> |"pipe &#124;"| area_n
       iso --> |"pipe &#124;"| sample_n
       line_b --> |"pipe &#124;"| Mean
       Directional --> |"pipe &#124;"| VolIntegrate
       Box --> |"pipe &#124;"| Mean
       area_n["area()"] --> |"pipe &#124;"| Sum
       sample_n["sample(mesh, field)"] --> |"pipe &#124;"| Mean
       VolIntegrate --> Table
       Sum --> Table
       Mean --> Table
       Min --> Table

**Builders** create datasets from OpenFOAM fields:

- ``field(mesh, "p")`` --- volume field (cell-centred values + cell volumes)
- ``iso_surface(mesh, "alpha.water", 0.5)`` --- iso-surface (face areas)
- ``line(mesh, "centreline", start, end, n, "p")`` --- line sample (interpolated values)

**Nodes** transform datasets before aggregation:

- ``Directional(bins, direction, origin)`` --- group cells into spatial bins
- ``Box(min, max)`` / ``Sphere(center, radius)`` --- spatial masks

**Aggregators** reduce datasets to scalar results:

- ``VolIntegrate`` --- sum weighted by cell volumes
- ``Sum``, ``Mean``, ``Min``, ``Max`` --- basic statistics
- ``SurfIntegrate`` --- sum weighted by face areas

The **pipe operator** ``|`` chains these together. ``PostProcessorBase`` with ``@Table`` decorators handles writing results to CSV at each timestep.

1. Create ``postProcess.py``
----------------------------

Place this file in your case directory (next to ``system/``):

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import area, field, iso_surface, residuals
   from pyOFTools.aggregators import VolIntegrate, Sum

   postProcess = PostProcessorBase()

   @postProcess.Table("vol_alpha.csv")
   def vol_alpha(mesh):
       """Volume integral of alpha.water at each timestep."""
       return field(mesh, "alpha.water") | VolIntegrate()

   @postProcess.Table("free_surface_area.csv")
   def free_surface_area(mesh):
       """Area of the alpha.water = 0.5 iso-surface."""
       return iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()

   @postProcess.Table("residuals.csv")
   def solver_residuals(mesh):
       """Solver residuals and iteration counts."""
       return residuals(mesh)

Each ``@postProcess.Table("filename.csv")`` decorator registers a computation. The function receives the mesh, builds a pipeline with the ``|`` operator, and pyOFTools handles the rest.

2. Wire it into ``controlDict``
-------------------------------

Add this to your ``system/controlDict``:

.. code-block:: c

   functions
   {
       pyPostProcessing
       {
           libs            ("libembeddingPython.so");
           type            pyPostProcessing;
           writeControl    timeStep;
           writeInterval   1;
           pyFileName      postProcess;
           pyClassName     postProcess;
       }
   }

3. Run your solver
------------------

.. code-block:: bash

   blockMesh
   setFields       # if needed
   interFoam       # or your solver

CSV files appear in ``postProcessing/``:

.. code-block:: text

   postProcessing/
   ├── vol_alpha.csv
   ├── free_surface_area.csv
   └── residuals.csv

4. Plot results
---------------

.. code-block:: python

   import pandas as pd
   import matplotlib.pyplot as plt

   df = pd.read_csv("postProcessing/vol_alpha.csv")
   plt.plot(df["time"], df["alpha.water_volIntegrate"])
   plt.xlabel("Time [s]")
   plt.ylabel("Water volume [m³]")
   plt.show()

Next steps
----------

- :doc:`tutorial/in-situ-post-processing` --- binning, mass distribution, multiple outputs
- :doc:`tutorial/field-statistics` --- aggregators (Sum, Mean, Min, Max) and spatial selectors
- :doc:`tutorial/sampling` --- sample along lines and surfaces
