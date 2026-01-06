"""
TableWriter for table output with format dispatch.

This module provides a TableWriter class that implements the PostProcessorInterface
protocol for writing workflow results to various table formats (CSV, DAT, etc.)
using Pydantic discriminated unions for format selection.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Annotated, Callable, Literal, Union

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pybFoam import fvMesh

    from ..workflow import WorkFlow

from .csvWriter import CSVWriter


class CSVFormatConfig(BaseModel):
    """Configuration for CSV format writer."""
    
    format: Literal["csv"] = "csv"
    file_path: str
    
    def create_writer(self) -> CSVWriter:
        """Create a CSVWriter instance."""
        return CSVWriter(file_path=self.file_path)


class DATFormatConfig(BaseModel):
    """Configuration for DAT format writer (alias for CSV)."""
    
    format: Literal["dat"] = "dat"
    file_path: str
    
    def create_writer(self) -> CSVWriter:
        """Create a CSVWriter instance (DAT uses CSV format)."""
        return CSVWriter(file_path=self.file_path)


# Discriminated union of all supported table formats
TableFormatConfig = Annotated[
    Union[CSVFormatConfig, DATFormatConfig],
    Field(discriminator="format")
]


class TableWriter:
    """
    Table writer with format dispatch implementing PostProcessorInterface.

    This writer dispatches to format-specific writers (CSV, DAT, etc.)
    based on file extension using Pydantic discriminated unions.
    It implements the OpenFOAM function object interface (execute, write, end)
    and handles write control logic.

    Args:
        mesh: OpenFOAM mesh object
        func: Workflow function to evaluate
        base_path: Base directory for output files
        filename: Output filename (extension determines format)
        writeControl: When to write ("writeTime" or "timeStep")
        writeInterval: Interval for writing (default: 1)

    Example:
        >>> def compute_mass(mesh):
        ...     return field(mesh, "rho") | VolIntegrate()
        >>> writer = TableWriter(
        ...     mesh=mesh,
        ...     func=compute_mass,
        ...     base_path="postProcessing/",
        ...     filename="results.csv",
        ...     writeControl="timeStep",
        ...     writeInterval=10
        ... )
        >>> writer.execute()
        >>> writer.write()
        >>> writer.end()
    """

    # Extension to format name mapping
    _extension_map = {
        ".csv": "csv",
        ".dat": "dat",
    }

    def __init__(
        self,
        mesh: fvMesh,
        func: Callable[[fvMesh], WorkFlow],
        base_path: str,
        filename: str,
        writeControl: str = "writeTime",
        writeInterval: int = 1,
    ):
        """Initialize TableWriter with configuration and format dispatch."""
        self.mesh = mesh
        self.func = func
        self.filename = filename
        self.write_control = writeControl
        self.write_interval = writeInterval
        self._step_count = 0

        # Extract file extension and map to format
        _, ext = os.path.splitext(filename)
        
        if ext not in self._extension_map:
            supported_formats = ", ".join(sorted(self._extension_map.keys()))
            raise ValueError(
                f"Unsupported file extension '{ext}'. "
                f"Supported formats: {supported_formats}"
            )
        
        format_name = self._extension_map[ext]
        file_path = f"{base_path}{filename}"
        
        # Create format config using discriminated union
        format_config: TableFormatConfig
        if format_name == "csv":
            format_config = CSVFormatConfig(file_path=file_path)
        elif format_name == "dat":
            format_config = DATFormatConfig(file_path=file_path)
        else:
            raise ValueError(f"Unknown format: {format_name}")
        
        # Create format writer
        self._format_writer = format_config.create_writer()
        self._format_writer.create_file()

    def execute(self) -> bool:
        """
        Execute method called each time step.

        Increments internal step counter for write control.

        Returns:
            True to indicate success
        """
        self._step_count += 1
        return True

    def write(self) -> bool:
        """
        Write method called when output should be written.

        Evaluates the workflow function and writes results if
        write control conditions are met.

        Returns:
            True to indicate success
        """
        # Check if we should write this output
        should_write = False
        if self.write_control == "writeTime":
            should_write = True
        elif self.write_control == "timeStep":
            should_write = (self._step_count % self.write_interval) == 0

        if should_write:
            current_time = self.mesh.time().value()
            workflow: WorkFlow = self.func(self.mesh)
            self._format_writer.write_data(time=current_time, workflow=workflow)

        return True

    def end(self) -> bool:
        """
        End method called at simulation end.

        Closes the format writer.

        Returns:
            True to indicate success
        """
        self._format_writer.close()
        return True
