"""Unit tests for SetInterpolator and create_set_dataset."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock pybFoam modules BEFORE any other imports
mock_pybfoam = MagicMock()
mock_pybfoam.vectorField = MagicMock
mock_pybfoam.scalarField = MagicMock
mock_pybfoam.Word = MagicMock
mock_pybfoam.boolList = MagicMock
sys.modules['pybFoam'] = mock_pybfoam

mock_sampling = MagicMock()
sys.modules['pybFoam.sampling'] = mock_sampling

# Now safe to import after mocking
from pyOFTools.set_interpolation import SetInterpolator, create_set_dataset


@pytest.fixture
def mock_scalar_field():
    """Create mock volScalarField."""
    mock_field = Mock()
    # Set __class__ to have proper name for isinstance checks
    mock_field.__class__ = type('volScalarField', (), {})
    return mock_field


@pytest.fixture
def mock_vector_field():
    """Create mock volVectorField."""
    mock_field = Mock()
    # Set __class__ to have proper name for isinstance checks
    mock_field.__class__ = type('volVectorField', (), {})
    return mock_field


@pytest.fixture
def mock_sampled_set():
    """Create mock sampledSet."""
    mock_set = Mock()
    mock_set.points.return_value = [Mock() for _ in range(10)]
    mock_set.cells.return_value = list(range(10))
    return mock_set


@pytest.fixture
def mock_sampled_set_with_data():
    """Create mock sampledSet with known data."""
    mock_set = Mock()
    mock_set.points.return_value = [Mock() for _ in range(5)]
    mock_set.distance.return_value = [0.0, 0.25, 0.5, 0.75, 1.0]
    mock_set.cells.return_value = [0, 1, 2, 3, 4]
    mock_set.name.return_value = "testSet"
    mock_set.axis.return_value = "distance"
    return mock_set


@pytest.fixture
def mock_field():
    """Create mock field."""
    mock_field = Mock()
    mock_field.__class__ = type('volScalarField', (), {})
    return mock_field


def test_default_scheme():
    """Test interpolator creation with default scheme."""
    interpolator = SetInterpolator()
    assert interpolator.scheme == "cellPoint"


def test_custom_scheme_cell():
    """Test interpolator with 'cell' scheme."""
    interpolator = SetInterpolator(scheme="cell")
    assert interpolator.scheme == "cell"


def test_custom_scheme_cellPoint():
    """Test interpolator with 'cellPoint' scheme."""
    interpolator = SetInterpolator(scheme="cellPoint")
    assert interpolator.scheme == "cellPoint"


def test_custom_scheme_cellPointFace():
    """Test interpolator with 'cellPointFace' scheme."""
    interpolator = SetInterpolator(scheme="cellPointFace")
    assert interpolator.scheme == "cellPointFace"


def test_invalid_scheme():
    """Test that invalid scheme raises ValueError."""
    with pytest.raises(ValueError, match="Invalid interpolation scheme"):
        SetInterpolator(scheme="invalidScheme")


def test_invalid_scheme_message():
    """Test error message contains valid options."""
    with pytest.raises(ValueError, match="cell.*cellPoint.*cellPointFace"):
        SetInterpolator(scheme="badScheme")


def test_interpolate_structure(mock_scalar_field, mock_sampled_set):
    """Test that interpolate is callable and returns result."""
    # Set the class name to match volScalarField for isinstance check
    type(mock_scalar_field).__name__ = 'volScalarField'
    
    interpolator = SetInterpolator(scheme="cellPoint")
    
    # Mock the sampling module
    with patch('pyOFTools.set_interpolation.sampling') as mock_sampling:
        mock_interp = Mock()
        mock_sampling.interpolationScalar.New.return_value = mock_interp
        mock_sampling.sampleSetScalar.return_value = Mock()
        
        # Mock volScalarField class for isinstance check
        with patch('pyOFTools.set_interpolation.volScalarField', Mock):
            result = interpolator.interpolate(mock_scalar_field, mock_sampled_set)
        
        # Verify interpolation was created with correct scheme
        mock_sampling.interpolationScalar.New.assert_called_once()
        mock_sampling.sampleSetScalar.assert_called_once()


def test_create_dataset_structure(mock_sampled_set_with_data, mock_field):
    """Test that create_set_dataset returns proper PointDataSet."""
    with patch('pyOFTools.set_interpolation.SetInterpolator') as MockInterpolator:
        mock_interpolator = Mock()
        mock_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        mock_interpolator.interpolate.return_value = mock_values
        MockInterpolator.return_value = mock_interpolator
        
        with patch('pyOFTools.set_interpolation.boolList') as mock_boolList:
            mock_boolList.return_value = [True] * 5
            
            dataset = create_set_dataset(
                mock_sampled_set_with_data,
                mock_field,
                name="test_dataset",
                scheme="cellPoint"
            )
            
            # Check dataset structure
            assert dataset.name == "test_dataset"
            assert dataset.field == mock_values
            assert dataset.geometry is not None


def test_create_dataset_with_mask(mock_sampled_set_with_data, mock_field):
    """Test dataset creation with invalid point masking."""
    # Mock some invalid cells
    mock_sampled_set_with_data.cells.return_value = [0, 1, -1, 3, -1]  # -1 = invalid
    
    with patch('pyOFTools.set_interpolation.SetInterpolator') as MockInterpolator:
        mock_interpolator = Mock()
        mock_interpolator.interpolate.return_value = [1.0, 2.0, 3.0, 4.0, 5.0]
        MockInterpolator.return_value = mock_interpolator
        
        with patch('pyOFTools.set_interpolation.boolList') as mock_boolList:
            created_mask = None
            def capture_mask(mask_list):
                nonlocal created_mask
                created_mask = mask_list
                return mask_list
            mock_boolList.side_effect = capture_mask
            
            dataset = create_set_dataset(
                mock_sampled_set_with_data,
                mock_field,
                name="masked_dataset",
                mask_invalid=True
            )
            
            # Verify mask was created for invalid points
            assert dataset.mask is not None
            assert created_mask == [True, True, False, True, False]


def test_create_dataset_without_mask(mock_sampled_set_with_data, mock_field):
    """Test dataset creation without masking."""
    with patch('pyOFTools.set_interpolation.SetInterpolator') as MockInterpolator:
        mock_interpolator = Mock()
        mock_interpolator.interpolate.return_value = [1.0, 2.0, 3.0, 4.0, 5.0]
        MockInterpolator.return_value = mock_interpolator
        
        dataset = create_set_dataset(
            mock_sampled_set_with_data,
            mock_field,
            name="no_mask_dataset",
            mask_invalid=False
        )
        
        # Verify no mask was created
        assert dataset.mask is None


def test_create_dataset_scheme_parameter(mock_sampled_set_with_data, mock_field):
    """Test that scheme parameter is passed to interpolator."""
    with patch('pyOFTools.set_interpolation.SetInterpolator') as MockInterpolator:
        mock_interpolator = Mock()
        mock_interpolator.interpolate.return_value = [1.0, 2.0, 3.0, 4.0, 5.0]
        MockInterpolator.return_value = mock_interpolator
        
        with patch('pyOFTools.set_interpolation.boolList'):
            dataset = create_set_dataset(
                mock_sampled_set_with_data,
                mock_field,
                name="test",
                scheme="cellPointFace"
            )
            
            # Verify interpolator was created with correct scheme
            MockInterpolator.assert_called_once_with(scheme="cellPointFace")
