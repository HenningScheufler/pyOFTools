.. _quickstart:


Quickstart
==========

This quickstart demonstrates how to use pyOFTools for post-processing OpenFOAM simulation data, using the damBreak example.

1. **Configure OpenFOAM case**
   - Add the following to your `system/controlDict`:

	 .. code-block:: foam

		functions
		{
			pyPostProcessing
			{
				libs            ("libembeddingPython.so");
				type            pyPostProcessing;
				writeControl    timeStep;
				writeInterval   1;
				pyFileName      postProcess;
				pyClassName     postProcess;
			}
		}

2. **Implement your Python post-processing class**

   Example: `postProcess.py` (located in `example/damBreak/postProcess.py`)

    Below is a breakdown of the post-processing class, with comments explaining each step:

    **Step-by-step breakdown:**

    1. **Initialization**: The `__init__` method sets up CSV writers for each output file. These files will store the results of the post-processing calculations.
    2. **Volume Calculation**: The first part of `write()` computes the total volume of water (`alpha.water`) in the domain and writes it to `vol_alpha.csv`.
    3. **Mass Distribution (Width)**: The second part bins the density field (`rho`) along the x-direction (width), integrates the mass in each bin, and writes the results to `mass.csv`.
    4. **Mass Distribution (Height)**: The third part bins the density field along the y-direction (height), integrates the mass in each bin, and writes the results to `mass_dist_height.csv`.
    5. **Each output is time-resolved**: The current simulation time is recorded for each output row.

    .. code-block:: python

        # Import required modules from pyOFTools and OpenFOAM Python bindings
        from pybFoam import volScalarField
        from pyOFTools.datasets import InternalDataSet
        from pyOFTools.geometry import FvMeshInternalAdapter
        from pyOFTools.writer import CSVWriter
        from pyOFTools.aggregators import VolIntegrate
        from pyOFTools.binning import Directional
        from pyOFTools.workflow import WorkFlow

        # Define the post-processing class that will be called by OpenFOAM
        class postProcess:
            def __init__(self, mesh):
                self.mesh = mesh  # Store mesh reference
                # Set up CSV writers for each output file
                self.volAlpha = CSVWriter(file_path="postProcessing/vol_alpha.csv")
                self.volAlpha.create_file()  # Create CSV file for volume of alpha.water
                self.mass = CSVWriter(file_path="postProcessing/mass.csv")
                self.mass.create_file()      # Create CSV file for mass distribution (width)
                self.mass_dist_height = CSVWriter(file_path="postProcessing/mass_dist_height.csv")
                self.mass_dist_height.create_file()  # Create CSV file for mass distribution (height)

            def write(self):
                # --- Calculate and write volume of alpha.water ---
                alpha = volScalarField.from_registry(self.mesh, "alpha.water")  # Get alpha.water field
                w_alpha = WorkFlow(
                    initial_dataset=InternalDataSet(
                        name="alpha_water",
                        field=alpha["internalField"],
                        geometry=FvMeshInternalAdapter(self.mesh),
                    )
                ).then(VolIntegrate())  # Integrate over the volume
                self.volAlpha.write_data(time=self.mesh.time().value(), workflow=w_alpha)

                # --- Calculate and write mass distribution along width ---
                rho = volScalarField.from_registry(self.mesh, "rho")  # Get density field
                w_mass = (
                    WorkFlow(
                        initial_dataset=InternalDataSet(
                            name="rho",
                            field=rho["internalField"],
                            geometry=FvMeshInternalAdapter(self.mesh),
                        )
                    )
                    .then(
                        Directional(
                            bins=[0.0, 0.146, 0.292, 0.438, 0.584],  # Bin edges along x-direction
                            direction=(1, 0, 0),
                            origin=(0, 0, 0),
                        )
                    )
                    .then(VolIntegrate())  # Integrate mass in each bin
                )
                self.mass.write_data(time=self.mesh.time().value(), workflow=w_mass)

                # --- Calculate and write mass distribution along height ---
                w_mass_height = (
                    WorkFlow(
                        initial_dataset=InternalDataSet(
                            name="rho",
                            field=rho["internalField"],
                            geometry=FvMeshInternalAdapter(self.mesh),
                        )
                    )
                    .then(
                        Directional(
                            bins=[0.0, 0.146, 0.292, 0.438, 0.584],  # Bin edges along y-direction
                            direction=(0, 1, 0),
                            origin=(0, 0, 0),
                        )
                    )
                    .then(VolIntegrate())
                )
                self.mass_dist_height.write_data(
                    time=self.mesh.time().value(), workflow=w_mass_height
                )

3. **Run your OpenFOAM simulation**
   - The post-processing will generate CSV files in the `postProcessing` directory.

4. **Plot results with Python**
   - Example: `plotResults.py`

	 .. code-block:: python

		import pandas as pd
		import seaborn as sns
		import matplotlib.pyplot as plt
		from pathlib import Path

		filepath = Path(__file__).parent
		vol_alpha = pd.read_csv(filepath / "postProcessing/vol_alpha.csv")
		sns.lineplot(data=vol_alpha, x="time", y="alpha_water_volIntegrate")
		plt.xlabel("Time [s]")
		plt.ylabel("Volume of water [m³]")
		plt.title("Volume of water over time")
		plt.grid()

		mass_width = pd.read_csv(filepath / "postProcessing/mass.csv")
		mass_width["group"] = mass_width["group"].map({1: "0-0.146m", 2: "0.146-0.292m", 3: "0.292-0.438m", 4: "0.438-0.584m"})
		plt.figure()
		sns.lineplot(data=mass_width, x="time", y="rho_volIntegrate", hue="group")
		plt.xlabel("Time [s]")
		plt.ylabel("Mass of water [kg]")
		plt.title("Mass of water over time")
		plt.grid()

		mass_height = pd.read_csv(filepath / "postProcessing/mass_dist_height.csv")
		mass_height["group"] = mass_height["group"].map({1: "0-0.146m", 2: "0.146-0.292m", 3: "0.292-0.438m", 4: "0.438-0.584m"})
		plt.figure()
		sns.lineplot(data=mass_height, x="time", y="rho_volIntegrate", hue="group")
		plt.xlabel("Time [s]")
		plt.ylabel("Mass of water [kg]")
		plt.title("Mass of water over time")
		plt.grid()
		plt.show()

Sampling Data Along a Line
--------------------------

This example demonstrates how to sample data along a line (e.g., a centerline) and export it.

.. code-block:: python

  from pybFoam import fvMesh, Time, volScalarField
  from pyOFTools.sets import create_uniform_set

  # Setup
  time = Time(".", ".")
  mesh = fvMesh(time)
  p = volScalarField.read_field(mesh, "p")

  # Create a centerline sample with 100 points
  dataset = create_uniform_set(
      mesh,
      name="centerline",
      start=(0.0, 0.0, 0.05),
      end=(0.584, 0.0, 0.05),
      n_points=100,
      field=p
  )

  # Access results
  positions = dataset.geometry.positions  # Point coordinates
  distances = dataset.geometry.distance   # Cumulative distance
  pressures = dataset.field               # Interpolated values
