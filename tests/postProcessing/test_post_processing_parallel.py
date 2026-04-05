"""
Parallel post-processing tests.

These run as normal serial pytest but the solver is executed in parallel
via AllrunParallel. They verify that pyPostProcessing produces correct
CSV output when running under MPI.
"""

import os

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


def test_parallel_csv_files_exist(run_reset_case_parallel, change_test_dir):
    """Test that all expected CSV files are created in parallel run."""
    csv_files = [
        "postProcessing/vol_alpha.csv",
        "postProcessing/mass.csv",
        "postProcessing/mass_dist_height.csv",
        "postProcessing/free_surface_area.csv",
        "postProcessing/residuals.csv",
    ]

    for csv_file in csv_files:
        assert os.path.exists(csv_file), f"CSV file {csv_file} was not created"


def test_parallel_vol_alpha_structure(run_reset_case_parallel, change_test_dir):
    """Test vol_alpha.csv has correct structure in parallel run."""
    df = pd.read_csv("postProcessing/vol_alpha.csv")

    assert list(df.columns) == ["time", "alpha.water_volIntegrate"]
    assert len(df) > 0
    assert df["time"].is_monotonic_increasing
    assert (df["alpha.water_volIntegrate"] > 0).all()
    assert (df["alpha.water_volIntegrate"] < 1).all()


def test_parallel_mass_structure(run_reset_case_parallel, change_test_dir):
    """Test mass.csv has correct structure in parallel run."""
    df = pd.read_csv("postProcessing/mass.csv")

    assert list(df.columns) == ["time", "rho_volIntegrate", "group"]
    assert len(df) > 0

    groups = sorted(df["group"].unique())
    assert len(groups) > 0
    assert (df["rho_volIntegrate"] >= 0).all()


def test_parallel_residuals(run_reset_case_parallel, change_test_dir):
    """Test residuals.csv has correct structure in parallel run."""
    df = pd.read_csv("postProcessing/residuals.csv")

    expected_columns = ["time", "residuals", "field", "solver", "metric", "iteration"]
    assert list(df.columns) == expected_columns
    assert len(df) > 0
    assert (df["residuals"] >= 0).all()
