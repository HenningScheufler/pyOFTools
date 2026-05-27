How-to guides
=============

Task-focused recipes. Read any of these independently — each solves one
specific problem. They assume you've worked through at least the first
tutorial. All examples run against the ``damBreak`` case shipped at
``examples/damBreak/``; :func:`pyOFTools.clone_example` copies it to a tmp
directory, then each script runs ``Allrun`` to generate the mesh and
initialise the alpha field before driving the workflow.

Prerequisites:

- OpenFOAM v2406+ sourced.
- ``blockMesh`` and ``pyoftools`` on ``PATH`` (the latter is the pyOFTools
  CLI, installed with the package).
- pybFoam and pyOFTools installed.
