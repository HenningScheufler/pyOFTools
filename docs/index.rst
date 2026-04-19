pyOFTools
=========

Python post-processing for OpenFOAM simulations.

pyOFTools lets you write in-situ post-processing in Python that runs inside your OpenFOAM solver. Define what to compute with a decorator, and pyOFTools handles field access, parallel reduction, and CSV output.

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import field
   from pyOFTools.aggregators import VolIntegrate

   postProcess = PostProcessorBase()

   @postProcess.Table("volume.csv")
   def water_volume(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

**Supported versions:** OpenFOAM 2406 / 2412 / 2506, Python 3.9--3.13

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   first-steps

.. toctree::
   :maxdepth: 2
   :caption: Tutorial

   tutorial/in-situ-post-processing
   tutorial/field-statistics
   tutorial/sampling
   tutorial/parallel

.. toctree::
   :maxdepth: 2
   :caption: Advanced

   advanced/custom-nodes
   advanced/workflow-internals

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/api

.. toctree::
   :maxdepth: 2
   :caption: How-To

   how-to/common-patterns
   how-to/troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
