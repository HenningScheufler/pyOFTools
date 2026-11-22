# Changelog

## [0.4.0]

Breaking changes:

* require Python 3.11 or newer
* require nanobind 3 (`nanobind>=3,<4`) to build
* require pybFoam 0.7.0 or newer at build time and at runtime
* link nanobind statically and use the header-only pybFoamEmbed target, so no
  shared library from pybFoam is needed at load time
