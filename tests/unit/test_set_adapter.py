"""Unit tests for SampledSetAdapter."""

import pytest
from unittest.mock import Mock, MagicMock
import sys

# Mock pybFoam modules BEFORE any other imports
mock_pybfoam = MagicMock()
mock_pybfoam.vectorField = MagicMock
mock_pybfoam.scalarField = MagicMock
sys.modules['pybFoam'] = mock_pybfoam
sys.modules['pybFoam.sampling'] = MagicMock()

# Now safe to import after mocking
from pyOFTools.geometry import SampledSetAdapter, SetGeometry


@pytest.fixture
def mock_sampled_set():
    """Create mock sampledSet."""
    mock_set = Mock()
    mock_set.points.return_value = Mock()
    mock_set.distance.return_value = Mock()
    mock_set.cells.return_value = [0, 1, 2, 3, 4]
    mock_set.faces.return_value = [-1, -1, -1, -1, -1]
    mock_set.segments.return_value = [0, 0, 0, 0, 0]
    mock_set.name.return_value = "testSet"
    mock_set.axis.return_value = "distance"
    return mock_set


@pytest.fixture
def mock_sampled_set_with_data():
    """Create mock sampledSet with known data."""
    mock_set = Mock()
    
    # Mock positions
    mock_positions = Mock()
    mock_positions.__len__ = Mock(return_value=5)
    mock_set.points.return_value = mock_positions
    
    # Mock distance
    mock_distance = [0.0, 0.25, 0.5, 0.75, 1.0]
    mock_set.distance.return_value = mock_distance
    
    # Mock other properties
    mock_set.cells.return_value = [0, 1, 2, 3, 4]
    mock_set.faces.return_value = [-1, -1, -1, -1, -1]
    mock_set.segments.return_value = [0, 0, 0, 0, 0]
    mock_set.name.return_value = "testLine"
    mock_set.axis.return_value = "distance"
    
    return mock_set


def test_protocol_conformance(mock_sampled_set):
    """Test that adapter conforms to SetGeometry protocol."""
    adapter = SampledSetAdapter(mock_sampled_set)
    assert isinstance(adapter, SetGeometry)


def test_has_positions_property(mock_sampled_set):
    """Test adapter has positions property."""
    adapter = SampledSetAdapter(mock_sampled_set)
    assert hasattr(adapter, 'positions')
    assert callable(getattr(type(adapter).positions, 'fget', None))


def test_has_distance_property(mock_sampled_set):
    """Test adapter has distance property."""
    adapter = SampledSetAdapter(mock_sampled_set)
    assert hasattr(adapter, 'distance')
    assert callable(getattr(type(adapter).distance, 'fget', None))


def test_positions_property(mock_sampled_set_with_data):
    """Test positions property returns sampled_set.points()."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    positions = adapter.positions
    
    assert positions is not None
    mock_sampled_set_with_data.points.assert_called()


def test_distance_property(mock_sampled_set_with_data):
    """Test distance property returns sampled_set.distance()."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    distance = adapter.distance
    
    assert distance == [0.0, 0.25, 0.5, 0.75, 1.0]
    mock_sampled_set_with_data.distance.assert_called()


def test_cells_property(mock_sampled_set_with_data):
    """Test cells property returns cell IDs."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    cells = adapter.cells
    
    assert cells == [0, 1, 2, 3, 4]
    mock_sampled_set_with_data.cells.assert_called()


def test_faces_property(mock_sampled_set_with_data):
    """Test faces property returns face IDs."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    faces = adapter.faces
    
    assert faces == [-1, -1, -1, -1, -1]
    mock_sampled_set_with_data.faces.assert_called()


def test_name_property(mock_sampled_set_with_data):
    """Test name property returns set name."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    name = adapter.name
    
    assert name == "testLine"


def test_axis_property(mock_sampled_set_with_data):
    """Test axis property returns axis type."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    axis = adapter.axis
    
    assert axis == "distance"


def test_nPoints_method(mock_sampled_set_with_data):
    """Test nPoints returns number of sample points."""
    adapter = SampledSetAdapter(mock_sampled_set_with_data)
    n = adapter.nPoints()
    
    assert n == 5


def test_adapter_caches_reference():
    """Test that adapter maintains reference to original set."""
    mock_set = Mock()
    mock_set.points.return_value = Mock()
    mock_set.distance.return_value = Mock()
    
    adapter = SampledSetAdapter(mock_set)
    
    # Access properties multiple times
    _ = adapter.positions
    _ = adapter.positions
    _ = adapter.distance
    
    # Verify underlying methods are called each time (not cached)
    assert mock_set.points.call_count == 2
    assert mock_set.distance.call_count == 1


def test_adapter_with_empty_set():
    """Test adapter with empty sampledSet."""
    mock_set = Mock()
    mock_positions = Mock()
    mock_positions.__len__ = Mock(return_value=0)
    mock_set.points.return_value = mock_positions
    mock_set.distance.return_value = []
    
    adapter = SampledSetAdapter(mock_set)
    
    assert adapter.nPoints() == 0
    assert adapter.distance == []
