Common Patterns
===============

Recipes for frequently needed post-processing tasks.

Mass conservation check
-----------------------

Track total mass over time to verify conservation:

.. code-block:: python

   @postProcess.Table("total_mass.csv")
   def total_mass(mesh):
       return field(mesh, "rho") | VolIntegrate()

For multiphase, track each phase:

.. code-block:: python

   @postProcess.Table("water_mass.csv")
   def water_mass(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

Volume-averaged field value
---------------------------

.. code-block:: python

   from pyOFTools.aggregators import Mean

   @postProcess.Table("avg_temperature.csv")
   def avg_T(mesh):
       return field(mesh, "T") | Mean()

Field extremes
--------------

.. code-block:: python

   from pyOFTools.aggregators import Min, Max

   @postProcess.Table("pressure_range.csv")
   def p_min(mesh):
       return field(mesh, "p") | Min()

   @postProcess.Table("pressure_max.csv")
   def p_max(mesh):
       return field(mesh, "p") | Max()

Spatial profile along a line
----------------------------

Sample pressure along a centreline and write to numpy for further analysis:

.. code-block:: python

   import numpy as np
   from pybFoam import fvMesh, Time, volScalarField
   from pyOFTools.sets import create_uniform_set

   time = Time(".", ".")
   mesh = fvMesh(time)
   p = volScalarField.read_field(mesh, "p")

   dataset = create_uniform_set(
       mesh, name="centreline",
       start=(0, 0, 0.05), end=(1, 0, 0.05),
       n_points=200, field=p,
   )

   x = np.asarray(dataset.geometry.distance)
   p_values = np.asarray(dataset.field)
   np.savetxt("centreline_p.dat", np.column_stack([x, p_values]))

Free surface area over time
----------------------------

.. code-block:: python

   from pyOFTools.builders import area, iso_surface
   from pyOFTools.aggregators import Sum

   @postProcess.Table("interface_area.csv")
   def interface_area(mesh):
       return iso_surface(mesh, "alpha.water", 0.5) | area() | Sum()

Average pressure on iso-surface
--------------------------------

.. code-block:: python

   from pyOFTools.builders import iso_surface, sample
   from pyOFTools.aggregators import Mean

   @postProcess.Table("surface_pressure.csv")
   def surface_pressure(mesh):
       return iso_surface(mesh, "alpha.water", 0.5) | sample(mesh, "p") | Mean()

Multiple statistics in one file
-------------------------------

Currently, each ``@Table`` decorator creates one output file. To compute multiple statistics, register multiple outputs:

.. code-block:: python

   @postProcess.Table("p_mean.csv")
   def p_mean(mesh):
       return field(mesh, "p") | Mean()

   @postProcess.Table("p_min.csv")
   def p_min(mesh):
       return field(mesh, "p") | Min()

   @postProcess.Table("p_max.csv")
   def p_max(mesh):
       return field(mesh, "p") | Max()
