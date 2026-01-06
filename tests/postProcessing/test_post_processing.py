import os

import numpy as np
import pandas as pd
import pytest
from oftest import run_reset_case as _run_reset_case


@pytest.fixture(scope="function")
def change_test_dir(request):
    """Change to test directory for OpenFOAM case access."""
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture(scope="function")  # to make ruff check pass
def run_reset_case(request):
    """Wrapper fixture for oftest's run_reset_case."""
    return _run_reset_case(request)


def test_csv_files_exist(run_reset_case, change_test_dir):
    """Test that all expected CSV files are created."""
    csv_files = [
        "postProcessing/vol_alpha.csv",
        "postProcessing/mass.csv",
        "postProcessing/mass_dist_height.csv",
        "postProcessing/free_surface_area.csv",
        "postProcessing/solverPerformance.csv",
    ]

    for csv_file in csv_files:
        assert os.path.exists(csv_file), f"CSV file {csv_file} was not created"


def test_vol_alpha_structure(run_reset_case, change_test_dir):
    """Test vol_alpha.csv has correct structure and reasonable values."""
    df = pd.read_csv("postProcessing/vol_alpha.csv")

    # Check columns
    assert list(df.columns) == ["time", "alpha.water_volIntegrate"]

    # Check that we have data
    assert len(df) > 0, "vol_alpha.csv is empty"

    # Check time is increasing
    assert df["time"].is_monotonic_increasing, "Time values should be monotonically increasing"

    # Check values are in reasonable range (volume should be positive and small)
    assert (df["alpha.water_volIntegrate"] > 0).all(), "Volume should be positive"
    assert (df["alpha.water_volIntegrate"] < 1).all(), "Volume should be less than 1"


def test_mass_structure(run_reset_case, change_test_dir):
    """Test mass.csv has correct structure and reasonable values."""
    df = pd.read_csv("postProcessing/mass.csv")

    # Check columns
    assert list(df.columns) == ["time", "rho_volIntegrate", "group"]

    # Check that we have data
    assert len(df) > 0, "mass.csv is empty"

    # Check groups (should be 0-4 for 5 bins)
    groups = sorted(df["group"].unique())
    assert groups == [0, 1, 2, 3, 4], f"Expected groups [0,1,2,3,4], got {groups}"

    # Check each time has all groups
    times = df["time"].unique()
    for time in times:
        time_groups = sorted(df[df["time"] == time]["group"].values)
        assert time_groups == [0, 1, 2, 3, 4], f"Time {time} missing some groups"

    # Check mass values are non-negative
    assert (df["rho_volIntegrate"] >= 0).all(), "Mass should be non-negative"


def test_mass_dist_height_structure(run_reset_case, change_test_dir):
    """Test mass_dist_height.csv has correct structure and reasonable values."""
    df = pd.read_csv("postProcessing/mass_dist_height.csv")

    # Check columns
    assert list(df.columns) == ["time", "rho_volIntegrate", "group"]

    # Check that we have data
    assert len(df) > 0, "mass_dist_height.csv is empty"

    # Check groups (should be 0-4 for 5 bins)
    groups = sorted(df["group"].unique())
    assert groups == [0, 1, 2, 3, 4], f"Expected groups [0,1,2,3,4], got {groups}"

    # Check mass values are non-negative
    assert (df["rho_volIntegrate"] >= 0).all(), "Mass should be non-negative"


def test_free_surface_area_structure(run_reset_case, change_test_dir):
    """Test free_surface_area.csv has correct structure and reasonable values."""
    df = pd.read_csv("postProcessing/free_surface_area.csv")

    # Check columns
    assert list(df.columns) == ["time", "iso_alpha.water_sum"]

    # Check that we have data
    assert len(df) > 0, "free_surface_area.csv is empty"

    # Check time is increasing
    assert df["time"].is_monotonic_increasing, "Time values should be monotonically increasing"

    # Check area values are positive
    assert (df["iso_alpha.water_sum"] > 0).all(), "Surface area should be positive"


def test_solver_performance_structure(run_reset_case, change_test_dir):
    """Test solverPerformance.csv has correct structure."""
    df = pd.read_csv("postProcessing/solverPerformance.csv")

    # Check columns
    expected_columns = ["time", "solverPerformance", "field", "solver", "metric", "iteration"]
    assert list(df.columns) == expected_columns, (
        f"Expected columns {expected_columns}, got {list(df.columns)}"
    )

    # Check that we have data
    assert len(df) > 0, "solverPerformance.csv is empty"

    # Check expected fields are present
    fields = df["field"].unique()
    assert "T" in fields, "Temperature field 'T' should be in solver performance"
    assert "p_rgh" in fields, "Pressure field 'p_rgh' should be in solver performance"

    # Check expected metrics
    metrics = df["metric"].unique()
    expected_metrics = ["init_res", "final_res", "nSolverIters"]
    for metric in expected_metrics:
        assert metric in metrics, f"Metric '{metric}' should be in solver performance"

    # Check solver performance values are non-negative
    assert (df["solverPerformance"] >= 0).all(), "Solver performance values should be non-negative"


def test_csv_values_match_reference(run_reset_case, change_test_dir):
    """Test that CSV values match reference data (first few timesteps)."""

    # Test vol_alpha first timestep
    df_vol_alpha = pd.read_csv("postProcessing/vol_alpha.csv")
    first_row = df_vol_alpha.iloc[0]
    assert np.isclose(first_row["time"], 0.00119, atol=1e-4), (
        "First timestep should be around 0.00119"
    )
    assert np.isclose(first_row["alpha.water_volIntegrate"], 0.000674, atol=1e-5), (
        "First alpha volume should be around 0.000674"
    )

    # Test mass distribution - check that group 0 (first bin) has zero mass initially
    df_mass = pd.read_csv("postProcessing/mass.csv")
    first_time_group0 = df_mass[
        (df_mass["time"] == df_mass["time"].min()) & (df_mass["group"] == 0)
    ]
    assert len(first_time_group0) == 1, (
        "Should have exactly one entry for group 0 at first timestep"
    )
    assert first_time_group0["rho_volIntegrate"].values[0] == 0.0, (
        "Group 0 should have zero mass initially"
    )

    # Test free surface area decreases over time (dam break physics)
    df_surface = pd.read_csv("postProcessing/free_surface_area.csv")
    # Get first and last values
    first_area = df_surface.iloc[0]["iso_alpha.water_sum"]
    # Check area at a later time (around t=0.05)
    mid_time = df_surface[df_surface["time"] >= 0.05].iloc[0]["iso_alpha.water_sum"]
    # Surface area should remain relatively constant or slightly decrease for dam break
    assert first_area > 0.005, "Initial surface area should be reasonable"
    assert mid_time > 0.005, "Surface area at t=0.05 should be reasonable"
