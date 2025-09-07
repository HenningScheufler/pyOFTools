[![Documentation](https://img.shields.io/readthedocs/pyOFTools)](https://pyOFTools.readthedocs.io/)
[![CI](https://github.com/HenningScheufler/pyOFTools/actions/workflows/ci.yml/badge.svg)](https://github.com/HenningScheufler/pyOFTools/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/HenningScheufler/pyOFTools/branch/main/graph/badge.svg)](https://codecov.io/gh/HenningScheufler/pyOFTools)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Publish](https://github.com/HenningScheufler/pyOFTools/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/HenningScheufler/pyOFTools/actions/workflows/pypi-publish.yml)
[![PyPI](https://img.shields.io/pypi/v/pyOFTools)](https://pypi.org/project/pyOFTools/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyOFTools)](https://pypi.org/project/pyOFTools/)
![OpenFOAM](https://img.shields.io/badge/openfoam-.com%20|%20.org-informational)



# pyOFTools

Python tools and utilities for OpenFOAM

Currently in the pre-alpha release state.

## Description

pyOFTools is a collection of Python utilities for working with OpenFOAM simulations. It provides:

- Region selection and geometry tools
- Field manipulation functions
- Post-processing utilities
- Time series analysis
- Dictionary handling

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenFOAM of2012 or higher (for OpenFOAM integration features)
- Required Python packages: numpy, pydantic

### Install from PyPI (when available)

```bash
pip install pyOFTools
```

### Install from source

```bash
git clone https://github.com/DLR-RY/pyOFTools.git
cd pyOFTools
pip install -e .
```

### Development installation

```bash
git clone https://github.com/DLR-RY/pyOFTools.git
cd pyOFTools
pip install -e ".[dev]"
```

## Usage

```python
import pyOFTools

# Use region selection tools
from pyOFTools import Box, Sphere

# Create geometric regions
box = Box(min=(0, 0, 0), max=(1, 1, 1))
sphere = Sphere(center=(0.5, 0.5, 0.5), radius=0.3)

# Combine regions
region = box & sphere  # intersection
```

## OpenFOAM Integration

The project also includes CMake build system for embedding Python into OpenFOAM as function objects. The CMake build is separate from the Python package installation.

## Testing

Run the test suite:

```bash
pytest
```

## Documentation

Documentation is work in progress and will be available at the project homepage.

## License

GPL-3.0-or-later