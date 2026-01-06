"""
Tests for PostProcessorBase decorator and registration system.
"""

from conftest import create_time_mesh

from pyOFTools.builders import field, residuals
from pyOFTools.postprocessor import PostProcessorBase


def test_postprocessor_base_initialization():
    """Test PostProcessorBase initialization."""
    processor = PostProcessorBase()
    assert processor._base_path == "postProcessing/"
    assert processor._outputs == {}


def test_postprocessor_base_custom_path():
    """Test PostProcessorBase with custom base path."""
    processor = PostProcessorBase(base_path="custom/path/")
    assert processor._base_path == "custom/path/"


def test_table_decorator_registers_function():
    """Test that @Table decorator registers functions."""
    processor = PostProcessorBase()

    @processor.Table("test.csv")
    def test_func(mesh):
        return field(mesh, "p")

    assert "test_func" in processor._outputs
    func, writer_cls, config = processor._outputs["test_func"]
    assert config["filename"] == "test.csv"
    assert func == test_func
    assert config.get("writeControl", "writeTime") == "writeTime"
    assert config.get("writeInterval", 1) == 1


def test_table_decorator_with_custom_params():
    """Test @Table decorator with custom parameters."""
    processor = PostProcessorBase()

    @processor.Table("output.csv", writeControl="timeStep", writeInterval=5)
    def custom_func(mesh):
        return field(mesh, "p")

    func, writer_cls, config = processor._outputs["custom_func"]
    assert config["filename"] == "output.csv"
    assert config["writeControl"] == "timeStep"
    assert config["writeInterval"] == 5


def test_table_decorator_multiple_functions():
    """Test registering multiple functions."""
    processor = PostProcessorBase()

    @processor.Table("file1.csv")
    def func1(mesh):
        return field(mesh, "p")

    @processor.Table("file2.csv")
    def func2(mesh):
        return field(mesh, "p")

    @processor.Table("file3.csv")
    def func3(mesh):
        return residuals(mesh)

    assert len(processor._outputs) == 3
    assert "func1" in processor._outputs
    assert "func2" in processor._outputs
    assert "func3" in processor._outputs


def test_bound_processor_creation(change_test_dir):
    """Test that calling PostProcessorBase creates a processor runner."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase(base_path="postProcessing/")

    @processor.Table("test.csv")
    def test_func(m):
        return field(m, "alpha.water")

    bound = processor(mesh)

    assert bound is not None
    assert bound.mesh == mesh
    assert hasattr(bound, "execute")
    assert hasattr(bound, "write")
    assert hasattr(bound, "end")


def test_bound_processor_execute_increments_step(change_test_dir):
    """Test that execute() delegates to writers."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase()

    @processor.Table("test.csv")
    def test_func(m):
        return field(m, "alpha.water")

    bound = processor(mesh)

    result = bound.execute()
    assert result is True
    # Verify writers exist
    assert len(bound._writers) == 1


def test_bound_processor_end_returns_true(change_test_dir):
    """Test that end() returns True."""
    _, mesh = create_time_mesh()
    
    processor = PostProcessorBase()

    @processor.Table("test.csv")
    def test_func(m):
        return field(m, "alpha.water")

    bound = processor(mesh)

    result = bound.end()
    assert result is True
