"""Integration tests for set sampling using cavity test case."""

import pytest
import os
import numpy as np
from pybFoam import Time, fvMesh, volScalarField, volVectorField, vector
from pyOFTools import (
    create_uniform_set,
    create_cloud_set,
    create_polyline_set,
    create_circle_set,
    SetInterpolator,
    SampledSetAdapter,
    create_set_dataset
)


@pytest.fixture(scope="module")
def cavity_case():
    """Get path to cavity test case."""
    case_path = os.path.join(os.path.dirname(__file__), "..", "cavity")
    if not os.path.exists(case_path):
        pytest.skip("Cavity test case not found")
    return case_path


@pytest.fixture(scope="module")
def cavity_mesh(cavity_case):
    """Create mesh from cavity case."""
    original_dir = os.getcwd()
    os.chdir(cavity_case)
    try:
        time = Time(".", ".")
        mesh = fvMesh(time)
        yield time, mesh
    finally:
        os.chdir(original_dir)


class TestSetCreation:
    """Test creating different types of sampledSets."""
    
    def test_create_uniform_set_cavity(self, cavity_mesh):
        """Test creating uniform line through cavity mesh."""
        time, mesh = cavity_mesh
        
        # Create diagonal line through cavity [0,1]x[0,1]
        line = create_uniform_set(
            mesh,
            name="diagonal",
            start=(0.0, 0.0, 0.005),
            end=(0.1, 0.1, 0.005),
            n_points=50,
            axis="distance"
        )
        
        assert line is not None
        assert line.name() == "diagonal"
        assert line.nPoints() > 0
        assert line.nPoints() <= 50
        assert line.axis() == "distance"
    
    def test_create_cloud_set_cavity(self, cavity_mesh):
        """Test creating cloud set in cavity mesh."""
        time, mesh = cavity_mesh
        
        # Create cloud at specific points
        cloud = create_cloud_set(
            mesh,
            name="probes",
            points=[
                (0.025, 0.025, 0.005),
                (0.05, 0.05, 0.005),
                (0.075, 0.075, 0.005)
            ],
            axis="xyz"
        )
        
        assert cloud is not None
        assert cloud.name() == "probes"
        assert cloud.nPoints() == 3
    
    def test_create_polyline_set_cavity(self, cavity_mesh):
        """Test creating polyLine path through cavity mesh."""
        time, mesh = cavity_mesh
        
        # Create L-shaped path
        polyline = create_polyline_set(
            mesh,
            name="Lpath",
            points=[
                (0.01, 0.01, 0.005),
                (0.09, 0.01, 0.005),
                (0.09, 0.09, 0.005)
            ],
            n_points=60,
            axis="distance"
        )
        
        assert polyline is not None
        assert polyline.name() == "Lpath"
        assert polyline.nPoints() > 0
        assert polyline.nPoints() <= 60
    
    def test_create_circle_set_cavity(self, cavity_mesh):
        """Test creating circle set in cavity mesh."""
        time, mesh = cavity_mesh
        
        # Create circle at center with small radius
        circle = create_circle_set(
            mesh,
            name="circle",
            origin=(0.05, 0.05, 0.005),
            axis=(0.0, 0.0, 1.0),
            start_point=(0.07, 0.05, 0.005),  # Radius = 0.02
            d_theta=10.0
        )
        
        assert circle is not None
        assert circle.name() == "circle"
        assert circle.nPoints() > 0


class TestFieldInterpolation:
    """Test interpolating fields onto sampledSets."""
    
    def test_interpolate_scalar_uniform_set_cavity(self, cavity_mesh):
        """Test interpolating scalar field onto uniform line."""
        time, mesh = cavity_mesh
        
        # Create synthetic field: p = x + y
        p = volScalarField.read_field(mesh, "p")
        cell_centers = mesh.C()["internalField"]
        p_internal = p["internalField"]
        
        for i in range(mesh.nCells()):
            cc = cell_centers[i]
            p_internal[i] = cc[0] + cc[1]
        
        # Create line along diagonal
        line = create_uniform_set(
            mesh, "diagonal",
            start=(0.0, 0.0, 0.005),
            end=(0.1, 0.1, 0.005),
            n_points=20
        )
        
        # Interpolate
        interpolator = SetInterpolator(scheme="cellPoint")
        values = interpolator.interpolate(p, line)
        
        # Check values increase along diagonal (p = x+y increases)
        values_array = np.asarray(values)
        assert len(values_array) > 0
        
        # Filter valid values
        valid_mask = values_array < 1e10
        valid_values = values_array[valid_mask]
        assert len(valid_values) > 0
        
        # Values should generally increase along diagonal
        if len(valid_values) > 1:
            assert np.mean(np.diff(valid_values)) > -1e-6
    
    def test_interpolate_vector_uniform_set_cavity(self, cavity_mesh):
        """Test interpolating vector field onto uniform line."""
        time, mesh = cavity_mesh
        
        # Create synthetic field: U = (x, y, 0)
        U = volVectorField.read_field(mesh, "U")
        cell_centers = mesh.C()["internalField"]
        U_internal = U["internalField"]
        
        for i in range(mesh.nCells()):
            cc = cell_centers[i]
            U_internal[i] = vector(cc[0], cc[1], 0.0)
        
        # Create line
        line = create_uniform_set(
            mesh, "line",
            start=(0.01, 0.01, 0.005),
            end=(0.09, 0.09, 0.005),
            n_points=25
        )
        
        # Interpolate
        interpolator = SetInterpolator(scheme="cellPoint")
        values = interpolator.interpolate(U, line)
        
        # Check we got vector values
        values_array = np.asarray(values)
        assert values_array.shape[1] == 3  # Vector field
        
        # Filter valid values
        valid_mask = np.all(values_array < 1e10, axis=1)
        valid_values = values_array[valid_mask]
        assert len(valid_values) > 0


class TestDifferentInterpolationSchemes:
    """Test different interpolation schemes."""
    
    @pytest.mark.parametrize("scheme", ["cell", "cellPoint", "cellPointFace"])
    def test_different_interpolation_schemes_cavity(self, cavity_mesh, scheme):
        """Test all interpolation schemes on cavity case."""
        time, mesh = cavity_mesh
        
        # Create field
        p = volScalarField.read_field(mesh, "p")
        cell_centers = mesh.C()["internalField"]
        p_internal = p["internalField"]
        for i in range(mesh.nCells()):
            p_internal[i] = float(i)
        
        # Create line
        line = create_uniform_set(
            mesh, "line",
            start=(0.02, 0.02, 0.005),
            end=(0.08, 0.08, 0.005),
            n_points=20
        )
        
        # Interpolate with specified scheme
        interpolator = SetInterpolator(scheme=scheme)
        values = interpolator.interpolate(p, line)
        
        values_array = np.asarray(values)
        assert len(values_array) > 0
        
        # Check all values are finite
        valid_mask = values_array < 1e10
        valid_values = values_array[valid_mask]
        assert len(valid_values) > 0
        assert np.all(np.isfinite(valid_values))


class TestSetDatasetCreation:
    """Test create_set_dataset convenience function."""
    
    def test_create_set_dataset_end_to_end_cavity(self, cavity_mesh):
        """Test complete workflow from set creation to dataset."""
        time, mesh = cavity_mesh
        
        # Create field
        p = volScalarField.read_field(mesh, "p")
        cell_centers = mesh.C()["internalField"]
        p_internal = p["internalField"]
        for i in range(mesh.nCells()):
            cc = cell_centers[i]
            p_internal[i] = cc[0] * 10.0  # Linear in x
        
        # Create line
        line = create_uniform_set(
            mesh, "centerline",
            start=(0.01, 0.05, 0.005),
            end=(0.09, 0.05, 0.005),
            n_points=30
        )
        
        # Create dataset
        dataset = create_set_dataset(
            line, p,
            name="pressure_centerline",
            scheme="cellPoint"
        )
        
        # Validate dataset
        assert dataset.name == "pressure_centerline"
        assert dataset.field is not None
        assert dataset.geometry is not None
        assert len(dataset.field) > 0
        assert len(dataset.geometry.positions) == len(dataset.field)
        assert len(dataset.geometry.distance) == len(dataset.field)
    
    def test_multiple_fields_same_set_cavity(self, cavity_mesh):
        """Test sampling multiple fields on same sampledSet."""
        time, mesh = cavity_mesh
        
        # Create two different fields
        p = volScalarField.read_field(mesh, "p")
        U = volVectorField.read_field(mesh, "U")
        
        cell_centers = mesh.C()["internalField"]
        p_internal = p["internalField"]
        U_internal = U["internalField"]
        
        for i in range(mesh.nCells()):
            cc = cell_centers[i]
            p_internal[i] = cc[0]
            U_internal[i] = vector(cc[1], 0.0, 0.0)
        
        # Create single sampledSet
        line = create_uniform_set(
            mesh, "line",
            start=(0.02, 0.02, 0.005),
            end=(0.08, 0.08, 0.005),
            n_points=15
        )
        
        # Sample both fields with same interpolator
        interpolator = SetInterpolator(scheme="cellPoint")
        sampled_p = interpolator.interpolate(p, line)
        sampled_U = interpolator.interpolate(U, line)
        
        # Both should have same length
        assert len(sampled_p) == line.nPoints()
        assert len(sampled_U) == line.nPoints()


class TestSampledSetAdapter:
    """Test SampledSetAdapter with real sampledSet."""
    
    def test_adapter_properties_cavity(self, cavity_mesh):
        """Test adapter provides correct properties."""
        time, mesh = cavity_mesh
        
        line = create_uniform_set(
            mesh, "test",
            start=(0.01, 0.01, 0.005),
            end=(0.09, 0.09, 0.005),
            n_points=20
        )
        
        adapter = SampledSetAdapter(line)
        
        # Test properties
        assert adapter.name == "test"
        assert adapter.axis == "distance"
        assert adapter.nPoints() > 0
        assert len(adapter.positions) == adapter.nPoints()
        assert len(adapter.distance) == adapter.nPoints()
        assert len(adapter.cells) == adapter.nPoints()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_set_outside_mesh_bounds_cavity(self, cavity_mesh):
        """Test handling sets extending outside mesh gracefully."""
        time, mesh = cavity_mesh
        
        # Create line that goes outside domain
        line = create_uniform_set(
            mesh, "outside",
            start=(0.05, 0.05, 0.005),
            end=(0.5, 0.5, 0.005),  # Extends beyond [0,0.1]
            n_points=20
        )
        
        # sampledSet should still be created
        assert line is not None
        # Will have fewer points since many are outside
        assert line.nPoints() > 0
        assert line.nPoints() <= 20
