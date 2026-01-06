"""
Basic tests for builder functions (field, iso_surface, residuals).
"""

from pybFoam import volScalarField

from pyOFTools.builders import field, iso_surface, residuals


def test_field_creates_workflow(time_mesh):
    """Test that field() creates a valid WorkFlow."""
    _, mesh = time_mesh

    # Load the field into registry
    volScalarField.read_field(mesh, "alpha.water")

    workflow = field(mesh, "alpha.water")

    assert workflow is not None
    assert hasattr(workflow, "compute")
    assert hasattr(workflow, "then")
    assert hasattr(workflow, "__or__")  # Pipe operator


def test_iso_surface_creates_workflow(time_mesh):
    """Test that iso_surface() creates a valid WorkFlow."""
    _, mesh = time_mesh

    workflow = iso_surface(mesh, "p", 0.0)

    assert workflow is not None
    assert hasattr(workflow, "compute")
    assert hasattr(workflow, "then")


def test_residuals_creates_workflow(time_mesh):
    """Test that residuals() creates a valid WorkFlow."""
    _, mesh = time_mesh

    workflow = residuals(mesh)

    assert workflow is not None
    assert hasattr(workflow, "compute")
