.. _core_concepts:

Core Concepts
=============

This section introduces the main building blocks of pyOFTools and how they work together to enable flexible, modular post-processing of OpenFOAM simulation data. The diagram below illustrates the typical workflow: data is wrapped, manipulated by nodes, and exported for further analysis.

.. mermaid::

	graph LR
		subgraph "Initial Data" 
			InternalDataSet[InternalDataSet]
		end
		subgraph "Nodes" 
			Directional[Directional]
			VolIntegrate[VolIntegrate]
		end
		subgraph "Writer" 
			CSVWriter[CSVWriter]
		end

		InternalDataSet --> Directional
		Directional --> VolIntegrate
		VolIntegrate --> CSVWriter

**Diagram Explanation**

This diagram shows the general workflow in pyOFTools:

- Data from OpenFOAM is wrapped in an `InternalDataSet` (initial data).
- The data is then manipulated by a series of nodes (such as `Directional` for binning and `VolIntegrate` for aggregation).
- Finally, the processed results are written out using a writer (e.g., `CSVWriter`).

This modular approach allows you to flexibly transform and analyze simulation data before exporting it for further use.

**General Workflow Example**

.. code-block:: python

	from pybFoam import volScalarField
	from pyOFTools.datasets import InternalDataSet
	from pyOFTools.geometry import FvMeshInternalAdapter
	from pyOFTools.writer import CSVWriter
	from pyOFTools.aggregators import VolIntegrate
	from pyOFTools.binning import Directional
	from pyOFTools.workflow import WorkFlow

	# Wrap OpenFOAM field and mesh
	alpha = volScalarField.from_registry(mesh, "alpha.water")
	dataset = InternalDataSet(
		 name="alpha_water",
		 field=alpha["internalField"],
		 geometry=FvMeshInternalAdapter(mesh),
	)

	# Build workflow: bin and integrate
	workflow = WorkFlow(initial_dataset=dataset)
	workflow = workflow.then(Directional(bins=[0, 0.1, 0.2], direction=(1,0,0), origin=(0,0,0)))
	workflow = workflow.then(VolIntegrate())

	# Export results
	writer = CSVWriter(file_path="postProcessing/alpha_bins.csv")
	writer.create_file()
	writer.write_data(time=mesh.time().value(), workflow=workflow)

**workflow**: Chains nodes to process the data step-by-step.

It transforms the initial dataset through a series of operations, ultimately producing the desired output.

**DataSet Classes**

pyOFTools provides several DataSet classes to represent different types of OpenFOAM data:

- **InternalDataSet**: Represents internal field data (e.g., cell-centered values) and mesh geometry. Used for most volume-based analyses.
- **PatchDataSet**: Handles data on boundary patches, such as wall or inlet/outlet fields.
- **SurfaceDataSet**: For surface field data, useful in cases with surface meshes or sampled surfaces.

.. code-block:: python

    name: str
    field: FieldType
    geometry: GeometricalInformation # surfaceMesh, volMesh
    mask: Optional[boolList] = None
    groups: Optional[labelList] = None

- **AggregatedDataSet**: Stores results of aggregation operations (e.g., integrated values, statistics) and considers the group and mask information.

Each DataSet class provides methods for accessing, filtering, and manipulating simulation data, making it easy to build flexible post-processing workflows.


**Nodes**
Nodes are modular operations that transform DataSets. For example, the `Directional` node segments data into bins along a specified direction (width or height), while `VolIntegrate` aggregates data by integrating over the mesh. Nodes are chained together to build a workflow.

**Writer**
Writers save the workflow results to files. The `CSVWriter` class exports processed results to CSV files. Each workflow writes its output (e.g., volume, mass distribution) to a separate file, making results easy to visualize and share.

