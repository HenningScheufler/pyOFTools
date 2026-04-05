"""
Output writers for post-processing.

This package contains implementations of the PostProcessorInterface protocol
for various output formats (CSV, VTK, HDF5, etc.).
"""

from .table import TableWriter

__all__ = [
    "TableWriter",
]
