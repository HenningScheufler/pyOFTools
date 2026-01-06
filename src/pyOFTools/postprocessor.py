"""
PostProcessor classes for decorator-based output registration.

This module provides the PostProcessorInterface protocol, PostProcessorBase,
and PostProcessorRunner classes for the simplified API with decorator-based
output registration and extensible writer components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, ClassVar, Dict, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pybFoam import fvMesh

    from .workflow import WorkFlow


__all__ = [
    "PostProcessorInterface",
    "PostProcessorBase",
    "PostProcessorRunner",
]


@runtime_checkable
class PostProcessorInterface(Protocol):
    """
    Protocol for post-processor output writers.

    This protocol defines the interface that all output writers must implement
    to be compatible with the PostProcessorBase registry system.

    Output writers are selected automatically based on file extension and must
    implement the OpenFOAM function object interface: execute(), write(), end().
    """

    def execute(self) -> bool:
        """
        Execute method called each time step.

        Returns:
            True to indicate success
        """
        ...

    def write(self) -> bool:
        """
        Write method called when output should be written.

        Returns:
            True to indicate success
        """
        ...

    def end(self) -> bool:
        """
        End method called at simulation end.

        Returns:
            True to indicate success
        """
        ...


class PostProcessorBase:
    """
    Base class for post-processor with decorator-based output registration.

    This class provides a decorator API for registering post-processing functions
    that will be called during simulation runtime. Output writers are selected
    automatically based on file extension.

    Args:
        base_path: Base directory for output files (default: "postProcessing/")

    Example:
        >>> postProcess = PostProcessorBase()
        >>>
        >>> @postProcess.Table("mass.csv")
        ... def total_mass(mesh):
        ...     return field(mesh, "rho") | VolIntegrate()
        >>>
        >>> # In OpenFOAM function object:
        >>> processor = postProcess(mesh)
        >>> processor.execute()  # Called each time step
        >>> processor.write()    # Called when writing output
        >>> processor.end()      # Called at end of simulation
    """

    def __init__(self, base_path: str = "postProcessing/"):
        """Initialize PostProcessorBase with output directory."""
        self._base_path = base_path
        self._outputs: Dict[str, tuple[Callable, type[PostProcessorInterface], Dict]] = {}

    def Table(
        self,
        filename: str,
        **kwargs,
    ) -> Callable:
        """
        Decorator to register a function as a table output.

        Uses TableWriter which dispatches to format-specific writers
        (CSV, HDF5, etc.) based on file extension.

        Args:
            filename: Output filename (extension determines format)
            **kwargs: Additional arguments passed to the writer (e.g., writeControl, writeInterval, format-specific options)

        Returns:
            Decorator function

        Example:
            >>> @postProcess.Table("results.csv", writeControl="timeStep", writeInterval=10)
            ... def compute_result(mesh):
            ...     return field(mesh, "p") | VolIntegrate()
        """
        from .tables.table import TableWriter

        def decorator(func: Callable) -> Callable:
            # Store writer class and config, func will be bound later with mesh
            self._outputs[func.__name__] = (func, TableWriter, {"filename": filename, **kwargs})
            return func

        return decorator

    def __call__(self, mesh: fvMesh) -> PostProcessorRunner:
        """
        Create a processor runner instance for the given mesh.

        Args:
            mesh: OpenFOAM mesh object

        Returns:
            PostProcessorRunner instance ready for use as OpenFOAM function object
        """
        return PostProcessorRunner(mesh, self._outputs, self._base_path)


class PostProcessorRunner:
    """
    Post-processor runner instance for executing registered outputs.

    This class implements the OpenFOAM function object interface (execute, write, end)
    and manages polymorphic output writers via the PostProcessorInterface protocol.

    Args:
        mesh: OpenFOAM mesh object
        outputs: Dictionary of registered output configurations (func, writer_cls, kwargs)
        base_path: Base directory for output files
    """

    def __init__(
        self,
        mesh: fvMesh,
        outputs: Dict[str, tuple[Callable, type[PostProcessorInterface], Dict]],
        base_path: str,
    ):
        """Initialize processor runner with mesh and output configurations."""
        self.mesh = mesh
        self._base_path = base_path

        # Instantiate writers from configurations
        self._writers: list[PostProcessorInterface] = []
        for name, (func, writer_cls, writer_kwargs) in outputs.items():
            writer = writer_cls(mesh=mesh, func=func, base_path=base_path, **writer_kwargs)
            self._writers.append(writer)

    def execute(self) -> bool:
        """
        Execute method called each time step.

        Delegates to all registered output writers.

        Returns:
            True to indicate success
        """
        for writer in self._writers:
            writer.execute()
        return True

    def write(self) -> bool:
        """
        Write method called when output should be written.

        Delegates to all registered output writers.

        Returns:
            True to indicate success
        """
        for writer in self._writers:
            writer.write()
        return True

    def end(self) -> bool:
        """
        End method called at simulation end.

        Delegates to all registered output writers for cleanup.

        Returns:
            True to indicate success
        """
        for writer in self._writers:
            writer.end()
        return True
