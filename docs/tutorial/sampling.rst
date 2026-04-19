Sampling
========

pyOFTools can sample fields along lines, on surfaces, and at arbitrary points. The results are returned as datasets that you can process further or export directly.

Line sampling
-------------

``create_uniform_set`` samples a field along a straight line with evenly spaced points:

.. code-block:: python

   from pybFoam import fvMesh, Time, volScalarField
   from pyOFTools.sets import create_uniform_set

   time = Time(".", ".")
   mesh = fvMesh(time)
   p = volScalarField.read_field(mesh, "p")

   dataset = create_uniform_set(
       mesh,
       name="centerline",
       start=(0.0, 0.0, 0.05),
       end=(0.584, 0.0, 0.05),
       n_points=100,
       field=p,
   )

   # Access results
   positions = dataset.geometry.positions   # point coordinates
   distances = dataset.geometry.distance    # cumulative distance along line
   values = dataset.field                   # interpolated field values

Other set types
^^^^^^^^^^^^^^^

.. code-block:: python

   from pyOFTools.sets import create_cloud_set, create_polyline_set, create_circle_set

   # Arbitrary point cloud
   cloud = create_cloud_set(
       mesh, name="probes",
       points=[(0.1, 0.1, 0.05), (0.2, 0.2, 0.05), (0.3, 0.3, 0.05)],
       field=p,
   )

   # Multi-segment polyline
   poly = create_polyline_set(
       mesh, name="path",
       points=[(0, 0, 0.05), (0.3, 0, 0.05), (0.3, 0.3, 0.05)],
       n_points=50,
       field=p,
   )

   # Circle
   circ = create_circle_set(
       mesh, name="ring",
       origin=(0.3, 0.3, 0.05),
       circle_axis=(0, 0, 1),
       start_point=(0.4, 0.3, 0.05),
       d_theta=5.0,
       field=p,
   )

Surface sampling
----------------

``create_plane`` creates a cutting plane and optionally interpolates a field onto it:

.. code-block:: python

   from pyOFTools.surfaces import create_plane

   surface_dataset = create_plane(
       mesh=mesh,
       name="midplane",
       point=(0.3, 0, 0),
       normal=(1, 0, 0),
       field=p,
   )

   positions = surface_dataset.geometry.positions
   areas = surface_dataset.geometry.face_area_magnitudes
   values = surface_dataset.field

Other surface types
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from pyOFTools.surfaces import (
       create_cutting_plane,
       create_iso_surface,
       create_patch_surface,
   )

   # Cutting plane (alternative algorithm)
   cutting = create_cutting_plane(
       mesh, name="cut", point=(0.3, 0, 0), normal=(1, 0, 0),
   )

   # Iso-surface of a scalar field
   iso = create_iso_surface(
       mesh=mesh, name="free_surface",
       field=alpha, iso_field_name="alpha.water", iso_value=0.5,
   )

   # Boundary patch as a surface
   wall = create_patch_surface(
       mesh, name="wall_surface", patches=["lowerWall"],
   )

Interpolation schemes
---------------------

All sampling functions accept a ``scheme`` parameter:

- ``"cellPoint"`` (default) --- interpolates using cell and point values
- ``"cell"`` --- nearest cell value (no interpolation)
- ``"cellPointFace"`` --- includes face values for better accuracy at boundaries

.. code-block:: python

   dataset = create_uniform_set(
       mesh, name="line", start=(0,0,0), end=(1,0,0),
       n_points=50, field=p, scheme="cell",
   )
