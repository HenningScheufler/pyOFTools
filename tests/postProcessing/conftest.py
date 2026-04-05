"""Shared fixtures for postProcessing tests."""

import subprocess

import pytest


@pytest.fixture(scope="function")
def run_reset_case(change_test_dir):
    """Reset OpenFOAM case before each test."""

    subprocess.run(["./Allclean"], check=True)
    subprocess.run(["./Allrun"], check=True)
    yield
    subprocess.run(["./Allclean"], check=True)


@pytest.fixture(scope="function")
def run_reset_case_parallel(change_test_dir):
    """Run OpenFOAM case in parallel, then clean up."""

    subprocess.run(["./Allclean"], check=True)
    subprocess.run(["./AllrunParallel"], check=True)
    yield
    subprocess.run(["./Allclean"], check=True)


# Re-export the fixture so it's available to tests in this directory
__all__ = ["run_reset_case", "run_reset_case_parallel"]
