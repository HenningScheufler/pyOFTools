.. _installation:


Installation
============

Prerequisites
-------------
Before installing pyOFTools, ensure you have the following:

- **OpenFOAM** (version 2406, 2412, or 2506 recommended)
- **Python** 3.9 or newer
- **pip** or **uv** for Python package management
- A C++ compiler (for building extensions, if needed)

Installation via pip or uv
-------------------------
You can install pyOFTools directly from PyPI using pip or uv. This will automatically download, install and compile pybFoam:

.. code-block:: bash

	pip install pyOFTools
	# or
	uv pip install pyOFTools

Installing from Source
----------------------
To install the latest development version, clone the repository and install in editable mode:

.. code-block:: bash

	git clone https://github.com/HenningScheufler/pyOFTools.git
	cd pyOFTools
	pip install -e .

Setting Up the Environment
-------------------------
If you are developing or running tests, install optional dependencies:

.. code-block:: bash

	pip install .[dev]

Make sure your Python environment is activated and OpenFOAM is available in your PATH. For OpenFOAM, source the appropriate bashrc, e.g.:

.. code-block:: bash

	source /opt/openfoam2406/etc/bashrc
