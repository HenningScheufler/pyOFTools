"""
Basic tests for builder functions (field, iso_surface, residuals).
"""

from pybFoam import volScalarField

from pyOFTools.builders import field, iso_surface, line, residuals


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


def test_line_creates_workflow(time_mesh):
    """Test that line() creates a valid WorkFlow with PointDataSet."""
    _, mesh = time_mesh

    workflow = line(mesh, "centreline", (0, 0, 0), (1, 1, 1), 10, "p")

    assert workflow is not None
    assert hasattr(workflow, "compute")
    assert hasattr(workflow, "__or__")


def test_line_with_aggregator(time_mesh):
    """Test that line() works with pipe operator."""
    from pyOFTools.aggregators import Mean

    _, mesh = time_mesh

    result = (line(mesh, "centreline", (0, 0, 0), (1, 1, 1), 10, "p") | Mean()).compute()

    assert result is not None
    assert len(result.values) > 0


def test_residuals_creates_workflow(time_mesh):
    """Test that residuals() creates a valid WorkFlow."""
    _, mesh = time_mesh

    workflow = residuals(mesh)

    assert workflow is not None
    assert hasattr(workflow, "compute")
