"""Global pytest configuration and fixtures"""
import pytest

# Import the patch before any tests run - this modifies pybFoam classes
# to automatically disable FPE trapping after OpenFOAM initialization
import pyOFTools.patch_pybfoam  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment at the start of the test session.
    
    The import of patch_pybfoam above ensures that pybFoam classes are
    patched to disable FPE trapping, preventing crashes when NumPy/pandas
    are used after OpenFOAM initialization.
    """
    yield
