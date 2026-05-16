pyOFTools
=========

Python post-processing for OpenFOAM simulations.

pyOFTools lets you write in-situ post-processing in Python that runs inside
your OpenFOAM solver. Define what to compute with a decorator, and pyOFTools
handles field access, parallel reduction, and CSV output.

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import field
   from pyOFTools.aggregators import VolIntegrate

   postProcess = PostProcessorBase()

   @postProcess.Table("volume.csv")
   def water_volume(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

**Supported versions:** OpenFOAM 2406 / 2412 / 2506, Python 3.9--3.13

.. admonition:: Which doc should I read?
   :class: tip

   * **New here?** Start with a tutorial — they walk through an end-to-end
     workflow.
   * **Have a specific task?** A how-to guide gives a step-by-step recipe.
   * **Looking up an API?** See the reference.
   * **Want the design?** Read the explanation section.

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   installation

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   auto_tutorials/example_01_setfields
   auto_tutorials/example_02_first_postprocessor
   auto_tutorials/example_03_profiles_and_selectors
   auto_tutorials/example_04_surface_monitors
   auto_tutorials/example_05_live_run_and_plot

.. toctree::
   :maxdepth: 1
   :caption: How-to guides

   auto_how_to/example_custom_aggregator
   auto_how_to/example_extract_residuals
   auto_how_to/example_iso_surface_area
   auto_how_to/example_sample_line
   auto_how_to/example_sample_plane
   auto_how_to/example_surface_integral
   auto_how_to/example_volume_integral
   how-to/configure_controlDict
   how-to/migrate_to_postprocessor_api
   how-to/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/api

.. toctree::
   :maxdepth: 2
   :caption: Explanation

   explanation/architecture
   explanation/datastructures
   explanation/workflow_internals
   explanation/custom_nodes

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
