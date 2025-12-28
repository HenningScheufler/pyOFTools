"""Unit tests for set factory functions."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock pybFoam modules BEFORE any other imports
mock_pybfoam = MagicMock()
mock_pybfoam.vectorField = MagicMock
mock_pybfoam.scalarField = MagicMock
mock_pybfoam.Word = MagicMock
mock_pybfoam.fvMesh = MagicMock
sys.modules['pybFoam'] = mock_pybfoam

mock_sampling = MagicMock()
mock_sampling.sampledSet = MagicMock
mock_sampling.meshSearch = MagicMock
mock_sampling.UniformSetConfig = MagicMock
mock_sampling.CloudSetConfig = MagicMock
mock_sampling.PolyLineSetConfig = MagicMock
mock_sampling.CircleSetConfig = MagicMock
sys.modules['pybFoam.sampling'] = mock_sampling

# Now safe to import after mocking
from pyOFTools.sets import (
    create_uniform_set,
    create_cloud_set,
    create_polyline_set,
    create_circle_set
)


@pytest.fixture
def mock_mesh():
    """Create mock OpenFOAM mesh."""
    return Mock()


@pytest.fixture
def mock_mesh_search():
    """Create mock meshSearch."""
    return Mock()


def test_create_uniform_set_basic(mock_mesh, mock_mesh_search):
    """Test basic uniform set creation."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            mock_set = Mock()
            mock_sampledSet.New.return_value = mock_set
            
            result = create_uniform_set(
                mesh=mock_mesh,
                name="line1",
                start=[0, 0, 0],
                end=[1, 0, 0],
                n_points=10
            )
            
            assert result is mock_set
            mock_sampledSet.New.assert_called_once()


def test_create_uniform_set_axis_parameter(mock_mesh, mock_mesh_search):
    """Test uniform set with axis parameter."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            with patch('pyOFTools.sets.Word') as mock_word:
                mock_set = Mock()
                mock_sampledSet.New.return_value = mock_set
                
                result = create_uniform_set(
                    mesh=mock_mesh,
                    name="line1",
                    start=[0, 0, 0],
                    end=[1, 0, 0],
                    n_points=10,
                    axis="xyz"
                )
                
                assert result is mock_set
                mock_word.assert_called()


def test_create_cloud_set_basic(mock_mesh, mock_mesh_search):
    """Test basic cloud set creation."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            mock_set = Mock()
            mock_sampledSet.New.return_value = mock_set
            
            points = [[0, 0, 0], [1, 1, 1], [2, 2, 2]]
            result = create_cloud_set(
                mesh=mock_mesh,
                name="cloud1",
                points=points
            )
            
            assert result is mock_set
            mock_sampledSet.New.assert_called_once()


def test_create_cloud_set_with_axis(mock_mesh, mock_mesh_search):
    """Test cloud set with axis parameter."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            with patch('pyOFTools.sets.Word') as mock_word:
                mock_set = Mock()
                mock_sampledSet.New.return_value = mock_set
                
                points = [[0, 0, 0], [1, 1, 1]]
                result = create_cloud_set(
                    mesh=mock_mesh,
                    name="cloud1",
                    points=points,
                    axis="distance"
                )
                
                assert result is mock_set


def test_create_polyline_set_basic(mock_mesh, mock_mesh_search):
    """Test basic polyline set creation."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            mock_set = Mock()
            mock_sampledSet.New.return_value = mock_set
            
            points = [[0, 0, 0], [1, 0, 0], [1, 1, 0]]
            result = create_polyline_set(
                mesh=mock_mesh,
                name="polyline1",
                points=points,
                n_points=20
            )
            
            assert result is mock_set
            mock_sampledSet.New.assert_called_once()


def test_create_polyline_set_with_axis(mock_mesh, mock_mesh_search):
    """Test polyline set with axis parameter."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            with patch('pyOFTools.sets.Word') as mock_word:
                mock_set = Mock()
                mock_sampledSet.New.return_value = mock_set
                
                points = [[0, 0, 0], [1, 0, 0]]
                result = create_polyline_set(
                    mesh=mock_mesh,
                    name="polyline1",
                    points=points,
                    n_points=10,
                    axis="xyz"
                )
                
                assert result is mock_set


def test_create_circle_set_basic(mock_mesh, mock_mesh_search):
    """Test basic circle set creation."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            mock_set = Mock()
            mock_sampledSet.New.return_value = mock_set
            
            result = create_circle_set(
                mesh=mock_mesh,
                name="circle1",
                origin=[0, 0, 0],
                axis=[0, 0, 1],
                start_point=[1, 0, 0],
                d_theta=10.0
            )
            
            assert result is mock_set
            mock_sampledSet.New.assert_called_once()


def test_create_circle_set_with_axis(mock_mesh, mock_mesh_search):
    """Test circle set with axis parameter."""
    with patch('pyOFTools.sets.sampledSet') as mock_sampledSet:
        with patch('pyOFTools.sets.meshSearch', return_value=mock_mesh_search):
            with patch('pyOFTools.sets.Word') as mock_word:
                mock_set = Mock()
                mock_sampledSet.New.return_value = mock_set
                
                result = create_circle_set(
                    mesh=mock_mesh,
                    name="circle1",
                    origin=[0, 0, 0],
                    axis=[0, 0, 1],
                    start_point=[1, 0, 0],
                    d_theta=10.0,
                    axis_type="distance"
                )
                
                assert result is mock_set
