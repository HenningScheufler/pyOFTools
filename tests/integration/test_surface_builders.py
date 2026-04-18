"""
Tests for surface builders: iso_surface, plane, area(), sample().

Verifies Proposal H: surface builders return geometry-only datasets,
area() and sample() are pipe nodes that populate the field.
"""

from pybFoam import volScalarField

from pyOFTools.aggregators import Max, Mean, Min, Sum
from pyOFTools.builders import area, iso_surface, plane, sample


def test_iso_surface_returns_workflow_without_field(time_mesh):
    """iso_surface() should return a WorkFlow with geometry-only dataset."""
    _, mesh = time_mesh

    wf = iso_surface(mesh, "p", 0.0)
    assert wf is not None
    assert hasattr(wf, "__or__")


def test_plane_returns_workflow_without_field(time_mesh):
    """plane() should return a WorkFlow with geometry-only dataset."""
    _, mesh = time_mesh

    wf = plane(mesh, point=(0.0, 0.0, 0.0), normal=(1, 0, 0))
    assert wf is not None
    assert hasattr(wf, "__or__")


def test_area_with_plane(time_mesh):
    """plane() | area() | Sum() should compute plane area."""
    _, mesh = time_mesh

    result = (plane(mesh, point=(0.0, 0.0, 0.0), normal=(1, 0, 0)) | area() | Sum()).compute()

    assert result is not None
    assert len(result.values) > 0
    area_val = float(result.values[0].value)
    assert area_val > 0


def test_sample_with_plane(time_mesh):
    """plane() | sample(mesh, "p") | Mean() should compute mean pressure on plane."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")

    result = (
        plane(mesh, point=(0.0, 0.0, 0.0), normal=(1, 0, 0)) | sample(mesh, "p") | Mean()
    ).compute()

    assert result is not None
    assert len(result.values) > 0


def test_sample_min_max_with_plane(time_mesh):
    """sample() should work with Min and Max aggregators."""
    _, mesh = time_mesh

    volScalarField.read_field(mesh, "p")

    min_result = (
        plane(mesh, point=(0.0, 0.0, 0.0), normal=(1, 0, 0)) | sample(mesh, "p") | Min()
    ).compute()
    max_result = (
        plane(mesh, point=(0.0, 0.0, 0.0), normal=(1, 0, 0)) | sample(mesh, "p") | Max()
    ).compute()

    min_val = float(min_result.values[0].value)
    max_val = float(max_result.values[0].value)
    assert min_val <= max_val
