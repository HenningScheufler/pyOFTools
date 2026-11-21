# Changelog

## [0.4.0]

Breaking changes:

* require Python 3.11 or newer
* require nanobind 3 (`nanobind>=3,<4`) to build
* require pybFoam 0.6.0 or newer at build time and at runtime

Other changes:

* add the `pythonMixed` boundary condition and `pyOFTools.bc`
* add `pyOFTools.parallel`, re-exporting the reductions of `pybFoam.parallel`
* fix the segfault of the embedded function object and boundary condition
  libraries under nanobind 3
