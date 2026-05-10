Migrate from the raw-WorkFlow API to ``@PostProcessorBase``
===========================================================

Early pyOFTools examples drove ``WorkFlow`` and ``CSVWriter`` manually from
an ``execute`` / ``write`` / ``end`` class. Since 0.3.0 the recommended
pattern is ``PostProcessorBase`` + ``@Table`` — less boilerplate, automatic
file lifecycle, parallel-safe writes. This recipe shows the mechanical port.

Before
------

The old ``example/damBreak/postProcess.py`` opened each file by hand and
drove a separate ``WorkFlow`` per output:

.. code-block:: python

   import pybFoam
   from pybFoam import volScalarField
   from pyOFTools.aggregators import VolIntegrate
   from pyOFTools.binning import Directional
   from pyOFTools.datasets import InternalDataSet
   from pyOFTools.geometry import FvMeshInternalAdapter
   from pyOFTools.tables.writer import CSVWriter
   from pyOFTools.workflow import WorkFlow


   class postProcess:
       def __init__(self, mesh: pybFoam.fvMesh):
           self.mesh = mesh
           self.volAlpha = CSVWriter(file_path="postProcessing/vol_alpha.csv")
           self.volAlpha.create_file()
           self.mass = CSVWriter(file_path="postProcessing/mass.csv")
           self.mass.create_file()

       def execute(self):
           pass

       def write(self):
           alpha = volScalarField.from_registry(self.mesh, "alpha.water")
           w_alpha = WorkFlow(
               initial_dataset=InternalDataSet(
                   name="alpha_water",
                   field=alpha["internalField"],
                   geometry=FvMeshInternalAdapter(self.mesh),
               )
           ).then(VolIntegrate())
           self.volAlpha.write_data(time=self.mesh.time().value(), workflow=w_alpha)

           rho = volScalarField.from_registry(self.mesh, "rho")
           w_mass = (
               WorkFlow(
                   initial_dataset=InternalDataSet(
                       name="rho",
                       field=rho["internalField"],
                       geometry=FvMeshInternalAdapter(self.mesh),
                   )
               )
               .then(Directional(bins=[0.0, 0.146, 0.292, 0.438, 0.584],
                                 direction=(1, 0, 0), origin=(0, 0, 0)))
               .then(VolIntegrate())
           )
           self.mass.write_data(time=self.mesh.time().value(), workflow=w_mass)

       def end(self):
           pass

After
-----

Same behaviour with the decorator API:

.. code-block:: python

   from pyOFTools.postprocessor import PostProcessorBase
   from pyOFTools.builders import field
   from pyOFTools.aggregators import VolIntegrate
   from pyOFTools.binning import Directional

   postProcess = PostProcessorBase()

   @postProcess.Table("vol_alpha.csv")
   def vol_alpha(mesh):
       return field(mesh, "alpha.water") | VolIntegrate()

   @postProcess.Table("mass.csv")
   def mass_distribution(mesh):
       return (
           field(mesh, "rho")
           | Directional(bins=[0.0, 0.146, 0.292, 0.438, 0.584],
                         direction=(1, 0, 0), origin=(0, 0, 0))
           | VolIntegrate()
       )

What changed, line by line
--------------------------

- **No ``__init__``, ``execute``, ``end``.** ``PostProcessorBase`` owns file
  creation and the function-object lifecycle.
- **No ``CSVWriter`` construction.** ``@postProcess.Table("vol_alpha.csv")``
  registers the output file; the framework builds the writer.
- **No ``InternalDataSet`` boilerplate.** ``field(mesh, "alpha.water")``
  does the ``volScalarField.from_registry`` lookup,
  ``FvMeshInternalAdapter`` wrap, and ``InternalDataSet`` construction in
  one call.
- **No manual ``write_data(time=..., workflow=...)``.** The framework
  passes the current time through automatically.
- **``|`` instead of ``.then(...)``.** The pipe operator is syntactic sugar
  for ``WorkFlow.then`` and reads top-to-bottom.

``system/controlDict`` does not need to change — the
``pyPostProcessing`` function object entry still refers to
``pyFileName postProcess`` and ``pyClassName postProcess``, and it now finds
a ``PostProcessorBase`` instance instead of a custom class. See
:doc:`configure_controlDict`.

When to keep the old pattern
----------------------------

Stay on the raw ``WorkFlow`` API if you need to:

- Drive the pipeline outside a running solver (standalone Python script) —
  though even there, the gallery scripts under :doc:`/auto_tutorials/index`
  show ``WorkFlow`` usage without the function-object wrapper.
- Use a dataset type the builders don't cover. Construct
  ``InternalDataSet`` / ``SurfaceDataSet`` / ``PointDataSet`` by hand and
  feed it into ``WorkFlow(initial_dataset=...)``.
- Share one opened file across multiple timesteps manually (uncommon —
  ``TableWriter`` already handles append-on-write).
