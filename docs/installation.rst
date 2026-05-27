Installation
============

Prerequisites
-------------

- **OpenFOAM** v2406, v2412, or v2506 (sourced in your shell)
- **Python** 3.9 or newer
- **C++ compiler** (for building the nanobind extension)

Source OpenFOAM before installing or using pyOFTools:

.. code-block:: bash

   source /opt/openfoam2406/etc/bashrc

Install
-------

.. code-block:: bash

   # From PyPI
   uv pip install pyOFTools

   # Or with pip
   pip install pyOFTools

From source (development):

.. code-block:: bash

   git clone https://github.com/HenningScheufler/pyOFTools.git
   cd pyOFTools
   uv pip install -e .[all]

Verify
------

.. code-block:: bash

   python -c "import pyOFTools; print(pyOFTools.__version__)"
