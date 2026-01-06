"""
Basic tests for builder functions (field, iso_surface, residuals).
"""

from conftest import create_time_mesh

from pyOFTools.builders import field, iso_surface, residuals


def test_field_creates_workflow(change_test_dir):
    """Test that field() creates a valid WorkFlow."""
    _, mesh = create_time_mesh()
    
    workflow = field(mesh, "alpha.water")

    assert workflow is not None
    assert hasattr(workflow, "compute")
    assert hasattr(workflow, "then")
    assert hasattr(workflow, "__or__")  # Pipe operator


def test_iso_surface_creates_workflow(change_test_dir):
    """Test that iso_surface() creates a valid WorkFlow."""
    _, mesh = create_time_mesh()
    
    workflow = iso_surface(mesh, "p", 0.0)

    assert workflow is not None
    assert hasattr(workflow, "compute")
    assert hasattr(workflow, "then")


def test_residuals_creates_workflow(change_test_dir):
    """Test that residuals() creates a valid WorkFlow."""
    _, mesh = create_time_mesh()
    
    workflow = residuals(mesh)

    assert workflow is not None
    assert hasattr(workflow, "compute")
