Changelog
=========

v0.4.0
------

Breaking changes:

- Require Python 3.11 or newer
- Require nanobind 3 (``nanobind>=3,<4``) to build
- Require pybFoam 0.6.0 or newer at build time and at runtime

Other changes:

- Add the ``pythonMixed`` boundary condition and ``pyOFTools.bc``
- Add ``pyOFTools.parallel``, re-exporting the reductions of ``pybFoam.parallel``
- Fix the segfault of the embedded function object and boundary condition
  libraries under nanobind 3

v0.2.0
------

- ``PostProcessorBase`` decorator API for in-situ post-processing
- Builder functions: ``field()``, ``iso_surface()``, ``residuals()``
- Pipe operator (``|``) for chaining workflow steps
- ``TableWriter`` with format dispatch (CSV, DAT)
- Parallel support: aggregation uses ``Foam::reduce()``, CSV writes only on master rank
- Spatial selectors: ``Box``, ``Sphere`` with boolean operators
- Sampling: ``create_uniform_set``, ``create_cloud_set``, ``create_polyline_set``, ``create_circle_set``
- Surfaces: ``create_plane``, ``create_cutting_plane``, ``create_iso_surface``, ``create_patch_surface``
- Aggregators: ``Sum``, ``Mean``, ``Min``, ``Max``, ``VolIntegrate``, ``SurfIntegrate``
- Binning: ``Directional`` node for spatial grouping
- Solver residual extraction
- OpenFOAM 2406, 2412, 2506 support
- Python 3.9--3.13 support
