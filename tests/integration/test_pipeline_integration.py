"""
Integration tests for pipeline operators and complete workflows.
"""

import os

from conftest import create_time_mesh

from pyOFTools.aggregators import Sum, VolIntegrate
from pyOFTools.builders import field, iso_surface, residuals
from pyOFTools.postprocessor import PostProcessorBase


def test_pipeline_operator_with_aggregator(change_test_dir):
    """Test that pipeline operator works with aggregators."""
    _, mesh = create_time_mesh()
    
    # Test pipeline with field | aggregator
    workflow = field(mesh, "alpha.water") | VolIntegrate()
    
    assert workflow is not None
    assert hasattr(workflow, "compute")
    
    # Verify it can compute
    result = workflow.compute()
    assert result is not None


def test_pipeline_with_multiple_aggregators(change_test_dir):
    """Test chaining multiple aggregators with pipeline operator."""
    from pyOFTools.binning import Directional
    
    _, mesh = create_time_mesh()
    
    # Test complex pipeline: field | binning | aggregator
    workflow = (
        field(mesh, "alpha.water")
        | Directional(
            bins=[0.0, 0.25, 0.5],
            direction=(1, 0, 0),
            origin=(0, 0, 0),
        )
        | VolIntegrate()
    )
    
    assert workflow is not None
    result = workflow.compute()
    assert result is not None


def test_decorator_with_pipeline_operator(change_test_dir):
    """Test that decorator works with pipeline operators."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase()

    @processor.Table("pipeline_test.csv")
    def test_pipeline(m):
        return field(m, "alpha.water") | VolIntegrate()

    bound = processor(mesh)
    
    # Verify the workflow is registered and can be executed
    assert "test_pipeline" in processor._outputs
    assert bound is not None


def test_iso_surface_with_pipeline(change_test_dir):
    """Test iso_surface with pipeline operator."""
    _, mesh = create_time_mesh()
    
    # Test iso_surface | Sum for area calculation
    workflow = iso_surface(mesh, "alpha.water", 0.5) | Sum()
    
    assert workflow is not None
    result = workflow.compute()
    assert result is not None


def test_complete_postprocessor_with_pipelines(change_test_dir):
    """Test complete post-processor setup with multiple pipeline workflows."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase(base_path="postProcessing/test/")

    @processor.Table("volume.csv")
    def volume(m):
        return field(m, "alpha.water") | VolIntegrate()

    @processor.Table("surface_area.csv")
    def surface_area(m):
        return iso_surface(m, "alpha.water", 0.5) | Sum()

    @processor.Table("residuals_data.csv")
    def residuals_data(m):
        return residuals(m)

    bound = processor(mesh)
    
    # Verify all workflows are registered
    assert len(processor._outputs) == 3
    assert "volume" in processor._outputs
    assert "surface_area" in processor._outputs
    assert "residuals_data" in processor._outputs
    
    # Verify bound processor has all writers
    assert len(bound._writers) == 3


def test_bound_processor_write_executes_pipeline(change_test_dir):
    """Test that write() executes pipeline and produces output."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase(base_path="postProcessing/pipeline_write_test/")

    @processor.Table("test_output.csv")
    def compute_volume(m):
        return field(m, "alpha.water") | VolIntegrate()

    bound = processor(mesh)
    
    # Execute and write
    bound.execute()
    result = bound.write()
    
    # Verify write returned True
    assert result is True
    
    # Verify CSV file was created
    csv_path = "postProcessing/pipeline_write_test/test_output.csv"
    assert os.path.exists(csv_path)
    
    # Verify file has content
    with open(csv_path, "r") as f:
        lines = f.readlines()
        assert len(lines) >= 2  # Header + at least one data line
        assert lines[0].startswith("time")  # Check header


def test_pipeline_operator_chaining_syntax(change_test_dir):
    """Test various pipeline chaining syntax patterns."""
    _, mesh = create_time_mesh()
    
    # Pattern 1: Simple field | aggregator
    w1 = field(mesh, "alpha.water") | VolIntegrate()
    result1 = w1.compute()
    assert result1 is not None
    
    # Pattern 2: iso_surface | aggregator  
    w2 = iso_surface(mesh, "alpha.water", 0.5) | Sum()
    result2 = w2.compute()
    assert result2 is not None
    
    # Pattern 3: Using then() method (equivalent to |)
    w3 = field(mesh, "p").then(VolIntegrate())
    result3 = w3.compute()
    assert result3 is not None
