Troubleshooting
===============

Floating point exception crash
-------------------------------

**Symptom:** Python crashes with a SIGFPE when importing numpy or pandas after OpenFOAM initialization.

**Cause:** OpenFOAM enables floating point exception trapping (``sigFpe``). numpy triggers FPE during initialization (e.g., testing for denormals).

**Fix:** pyOFTools patches this automatically via ``pyOFTools.patch_pybfoam``, which is imported by the test conftest. If you're using pybFoam directly without pyOFTools, disable FPE manually:

.. code-block:: python

   import pyOFTools.patch_pybfoam  # import before numpy

"cannot find file controlDict"
------------------------------

**Symptom:** ``FOAM FATAL ERROR: cannot find file "./system/controlDict"``

**Cause:** The Python script is not running from the case directory, or ``Time(".", ".")`` is called from the wrong working directory.

**Fix:** Ensure you ``cd`` to the case directory before running, or use absolute paths.

"field not found" or "no object registered"
-------------------------------------------

**Symptom:** ``KeyError`` or OpenFOAM error when accessing a field.

**Cause:** The field hasn't been read into the registry yet.

**Fix:** Call ``volScalarField.read_field(mesh, "fieldName")`` before using ``field(mesh, "fieldName")``. In-situ post-processing (via ``pyPostProcessing``) has fields available automatically because the solver reads them.

CSV files not created
---------------------

**Symptom:** No files appear in ``postProcessing/``.

**Possible causes:**

1. **``pyFileName`` or ``pyClassName`` wrong in controlDict** --- check that the module and object names match your Python file.
2. **Python file not on sys.path** --- the file must be in the case directory (where you run the solver from).
3. **Write control** --- if using ``writeControl: writeTime``, files are only written at OpenFOAM write intervals.

CSV files empty or corrupted in parallel
----------------------------------------

**Symptom:** CSV has duplicate rows or garbled content in parallel runs.

**Cause:** An older version of pyOFTools didn't guard file writes by MPI rank. All ranks wrote to the same file.

**Fix:** Update to the latest pyOFTools. The ``TableWriter`` now only writes on the master rank (``Pstream.master()``). The aggregation results are globally reduced, so the master has the correct values.

OpenFOAM not found
------------------

**Symptom:** ``ImportError`` when importing pybFoam, or build fails with "OpenFOAM not found".

**Fix:** Source the OpenFOAM environment before installing or running:

.. code-block:: bash

   source /opt/openfoam2406/etc/bashrc
   uv pip install pyOFTools
