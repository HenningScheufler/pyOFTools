from typing import Protocol, runtime_checkable

from pybFoam import fvMesh, scalarField, vectorField


@runtime_checkable
class InternalMesh(Protocol):
    @property
    def positions(self) -> vectorField: ...

    @property
    def volumes(self) -> scalarField: ...


@runtime_checkable
class BoundaryMesh(Protocol):
    @property
    def positions(self) -> vectorField: ...


@runtime_checkable
class SurfaceMesh(Protocol):
    """Protocol for surface meshes with geometry information."""
    
    @property
    def positions(self) -> vectorField:
        """Face center positions of the surface."""
        ...
    
    @property
    def face_areas(self) -> vectorField:
        """Face area vectors."""
        ...
    
    @property
    def face_area_magnitudes(self) -> scalarField:
        """Face area magnitudes."""
        ...
    
    @property
    def total_area(self) -> float:
        """Total surface area."""
        ...


@runtime_checkable
class SetGeometry(Protocol):
    """
    Protocol for sampled set geometry.
    
    Represents the geometric information of a sampledSet: an ordered collection
    of sample points (along lines, curves, or clouds) with a distance metric.
    Not a mesh in the connectivity sense, but a geometric point collection.
    """
    
    @property
    def positions(self) -> vectorField:
        """Sample point positions in 3D space."""
        ...
    
    @property
    def distance(self) -> scalarField:
        """Cumulative distance along the set (or arbitrary metric for clouds)."""
        ...



class SampledSurfaceAdapter:
    """
    Adapter for OpenFOAM sampledSurface to provide SurfaceMesh protocol.
    
    This adapter wraps a pybFoam.sampling.sampledSurface instance and provides
    a convenient interface for accessing surface geometry information.
    
    Example:
        >>> from pybFoam import sampling, fvMesh, Time, dictionary, word, vector
        >>> from pyOFTools.geometry import SampledSurfaceAdapter
        >>> 
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>> 
        >>> # Create a plane surface
        >>> plane_dict = dictionary()
        >>> plane_dict.set("type", word("plane"))
        >>> plane_dict.set("basePoint", vector(0.5, 0, 0))
        >>> plane_dict.set("normalVector", vector(1, 0, 0))
        >>> 
        >>> surface = sampling.sampledPlane(word("myPlane"), mesh, plane_dict)
        >>> adapter = SampledSurfaceAdapter(surface)
        >>> 
        >>> # Access geometry
        >>> face_centers = adapter.positions
        >>> area = adapter.total_area
    """
    
    def __init__(self, surface):
        """
        Initialize adapter with a sampledSurface instance.
        
        Args:
            surface: An instance of pybFoam.sampling.sampledSurface
        """
        self._surface = surface
        # Ensure surface is up-to-date
        if self._surface.needsUpdate():
            self._surface.update()
    
    @property
    def positions(self) -> vectorField:
        """Return face center positions of the surface."""
        return self._surface.Cf()
    
    @property
    def face_areas(self) -> vectorField:
        """Return face area vectors."""
        return self._surface.Sf()
    
    @property
    def face_area_magnitudes(self) -> scalarField:
        """Return face area magnitudes."""
        return self._surface.magSf()
    
    @property
    def points(self) -> vectorField:
        """Return surface points (vertices)."""
        return self._surface.points()
    
    @property
    def face_centers(self) -> vectorField:
        """Return face center positions (same as positions)."""
        return self.positions
    
    @property
    def total_area(self) -> float:
        """Return total surface area."""
        return self._surface.area()
    
    def update(self) -> bool:
        """
        Update surface if needed.
        
        Returns:
            True if surface was updated, False otherwise.
        """
        return self._surface.update()
    
    @property
    def name(self) -> str:
        """Return the name of the surface."""
        return str(self._surface.name())


class SampledSetAdapter:
    """
    Adapter for OpenFOAM sampledSet to provide SetGeometry protocol.
    
    This adapter wraps a pybFoam.sampling.sampledSet instance and provides
    a convenient interface for accessing set geometry information (points and distance).
    
    Example:
        >>> from pybFoam import fvMesh, Time
        >>> from pybFoam.sampling import meshSearch, sampledSet, UniformSetConfig
        >>> from pyOFTools.geometry import SampledSetAdapter
        >>> 
        >>> time = Time(".", ".")
        >>> mesh = fvMesh(time)
        >>> search = meshSearch(mesh)
        >>> 
        >>> # Create a line sampledSet
        >>> config = UniformSetConfig(
        ...     axis="distance",
        ...     start=[0, 0, 0],
        ...     end=[1, 0, 0],
        ...     nPoints=50
        ... )
        >>> set_dict = config.to_foam_dict()
        >>> line = sampledSet.New("myLine", mesh, search, set_dict)
        >>> 
        >>> # Wrap in adapter
        >>> adapter = SampledSetAdapter(line)
        >>> 
        >>> # Access geometry
        >>> positions = adapter.positions  # vectorField of sample points
        >>> distances = adapter.distance   # scalarField of cumulative distances
    """
    
    def __init__(self, sampled_set):
        """
        Initialize adapter with a sampledSet instance.
        
        Args:
            sampled_set: An instance of pybFoam.sampling.sampledSet
        """
        self._set = sampled_set
    
    @property
    def positions(self) -> vectorField:
        """Return sample point positions."""
        return self._set.points()
    
    @property
    def distance(self) -> scalarField:
        """Return cumulative distance along the set."""
        return self._set.distance()
    
    @property
    def cells(self):
        """Return cell IDs for each sample point."""
        return self._set.cells()
    
    @property
    def faces(self):
        """Return face IDs for each sample point (-1 if not on face)."""
        return self._set.faces()
    
    @property
    def segments(self):
        """Return segment numbers for each point (for polyLine sets)."""
        return self._set.segments()
    
    @property
    def name(self) -> str:
        """Return the name of the set."""
        return str(self._set.name())
    
    @property
    def axis(self) -> str:
        """Return the axis type (x, y, z, xyz, distance)."""
        return str(self._set.axis())
    
    def nPoints(self) -> int:
        """Return number of sample points."""
        return len(self.positions)


class FvMeshInternalAdapter:
    def __init__(self, mesh: "fvMesh") -> None:
        self._mesh = mesh

    @property
    def positions(self) -> vectorField:
        return self._mesh.C()["internalField"]

    @property
    def volumes(self) -> scalarField:
        return self._mesh.V()
