#!/usr/bin/env python3
"""
Example demonstrating surface mesh support in pyOFTools.

This example shows how to:
1. Create various types of surfaces (plane, patch, iso-surface, etc.)
2. Interpolate OpenFOAM fields onto surfaces
3. Create SurfaceDataSet objects for further analysis
4. Calculate statistics and visualize surface data

Usage:
    python surface_example.py [--case /path/to/case] [--time latest]
"""

import argparse
import sys
from pathlib import Path

try:
    from pybFoam import Time, argList, createMesh, volScalarField, volVectorField
    import pyOFTools
    from pyOFTools import (
        create_plane_surface,
        create_patch_surface,
        create_iso_surface,
        create_cutting_plane,
        SampledSurfaceAdapter,
        SurfaceInterpolator,
        create_interpolated_dataset,
    )

    PYBFOAM_AVAILABLE = True
except ImportError as e:
    print(f"Error: Required packages not available: {e}")
    print("Please ensure pybFoam and pyOFTools are installed.")
    sys.exit(1)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demonstrate surface mesh support in pyOFTools"
    )
    parser.add_argument(
        "--case",
        type=str,
        default="./example/damBreak",
        help="Path to OpenFOAM case (default: ./example/damBreak)",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="latest",
        help="Time to process (default: latest)",
    )
    return parser.parse_args()


def initialize_case(case_path: str):
    """
    Initialize OpenFOAM case.

    Args:
        case_path: Path to OpenFOAM case directory

    Returns:
        tuple: (runTime, mesh) objects
    """
    print(f"\n{'='*60}")
    print(f"Initializing OpenFOAM case: {case_path}")
    print(f"{'='*60}")

    # Create argList and Time
    args = argList(["solver", "-case", case_path])
    runTime = Time(args)

    # Create mesh
    mesh = createMesh(runTime)

    print(f"✓ Mesh loaded: {mesh.nCells()} cells, {mesh.nPoints()} points")

    return runTime, mesh


def set_time(runTime, time_spec: str = "latest"):
    """
    Set the time for the case.

    Args:
        runTime: OpenFOAM Time object
        time_spec: Either "latest" or a specific time value
    """
    times = runTime.times()

    if time_spec == "latest":
        time_idx = times.size() - 1
    else:
        # Find closest time
        target = float(time_spec)
        time_idx = 0
        min_diff = abs(float(times[0].value()) - target)
        for i in range(1, times.size()):
            diff = abs(float(times[i].value()) - target)
            if diff < min_diff:
                min_diff = diff
                time_idx = i

    runTime.setTime(times[time_idx], time_idx)
    print(f"✓ Time set to: {times[time_idx].value()}")


def demonstrate_surface_creation(mesh):
    """
    Demonstrate creating various types of surfaces.

    Args:
        mesh: OpenFOAM mesh object

    Returns:
        dict: Dictionary of created surfaces
    """
    print(f"\n{'='*60}")
    print("Creating Various Surface Types")
    print(f"{'='*60}")

    surfaces = {}

    # 1. Plane surface
    print("\n1. Creating plane surface (x=0.292)...")
    surfaces["plane_x"] = create_plane_surface(
        mesh=mesh,
        name="plane_x",
        base_point=(0.292, 0.0, 0.0),
        normal=(1.0, 0.0, 0.0),
    )
    print(
        f"   ✓ Plane created: {len(surfaces['plane_x'].points())} points, "
        f"{len(surfaces['plane_x'].faces())} faces"
    )

    # 2. Patch surface
    print("\n2. Creating patch surface (leftWall)...")
    surfaces["patch"] = create_patch_surface(
        mesh=mesh, name="leftWall_surface", patches=["leftWall"]
    )
    print(
        f"   ✓ Patch surface created: {len(surfaces['patch'].points())} points, "
        f"{len(surfaces['patch'].faces())} faces"
    )

    # 3. Cutting plane
    print("\n3. Creating cutting plane (y-direction)...")
    surfaces["cutting_plane"] = create_cutting_plane(
        mesh=mesh,
        name="cutting_plane_y",
        base_point=(0.0, 0.292, 0.0),
        normal=(0.0, 1.0, 0.0),
    )
    print(
        f"   ✓ Cutting plane created: {len(surfaces['cutting_plane'].points())} points, "
        f"{len(surfaces['cutting_plane'].faces())} faces"
    )

    # 4. Iso-surface (alpha.water = 0.5)
    print("\n4. Creating iso-surface (alpha.water = 0.5)...")
    try:
        surfaces["iso"] = create_iso_surface(
            mesh=mesh, name="alpha_interface", field_name="alpha.water", iso_value=0.5
        )
        print(
            f"   ✓ Iso-surface created: {len(surfaces['iso'].points())} points, "
            f"{len(surfaces['iso'].faces())} faces"
        )
    except Exception as e:
        print(f"   ⚠ Could not create iso-surface: {e}")

    return surfaces


def demonstrate_field_interpolation(mesh, runTime, surface):
    """
    Demonstrate interpolating fields onto a surface.

    Args:
        mesh: OpenFOAM mesh object
        runTime: OpenFOAM Time object
        surface: sampledSurface object

    Returns:
        dict: Dictionary of interpolated fields
    """
    print(f"\n{'='*60}")
    print("Interpolating Fields onto Surface")
    print(f"{'='*60}")

    interpolator = SurfaceInterpolator(mesh, interpolation_scheme="cellPoint")
    interpolated_fields = {}

    # Try to interpolate pressure
    print("\n1. Interpolating pressure field...")
    try:
        p_field = volScalarField.New(runTime, mesh, "p")
        p_interp = interpolator.interpolate_scalar(p_field, surface)
        interpolated_fields["p"] = p_interp

        # Calculate statistics
        p_values = [float(p_interp[i]) for i in range(len(p_interp))]
        p_min = min(p_values)
        p_max = max(p_values)
        p_mean = sum(p_values) / len(p_values)

        print(f"   ✓ Pressure interpolated: {len(p_interp)} values")
        print(f"   Statistics: min={p_min:.6f}, max={p_max:.6f}, mean={p_mean:.6f}")
    except Exception as e:
        print(f"   ⚠ Could not interpolate pressure: {e}")

    # Try to interpolate velocity
    print("\n2. Interpolating velocity field...")
    try:
        U_field = volVectorField.New(runTime, mesh, "U")
        U_interp = interpolator.interpolate_vector(U_field, surface)
        interpolated_fields["U"] = U_interp

        # Calculate velocity magnitudes
        U_mag = [
            float((U_interp[i].x() ** 2 + U_interp[i].y() ** 2 + U_interp[i].z() ** 2) ** 0.5)
            for i in range(len(U_interp))
        ]
        U_mag_max = max(U_mag)
        U_mag_mean = sum(U_mag) / len(U_mag)

        print(f"   ✓ Velocity interpolated: {len(U_interp)} values")
        print(f"   Statistics: max_mag={U_mag_max:.6f}, mean_mag={U_mag_mean:.6f}")
    except Exception as e:
        print(f"   ⚠ Could not interpolate velocity: {e}")

    # Try to interpolate alpha.water
    print("\n3. Interpolating alpha.water field...")
    try:
        alpha_field = volScalarField.New(runTime, mesh, "alpha.water")
        alpha_interp = interpolator.interpolate_scalar(alpha_field, surface)
        interpolated_fields["alpha.water"] = alpha_interp

        alpha_values = [float(alpha_interp[i]) for i in range(len(alpha_interp))]
        alpha_min = min(alpha_values)
        alpha_max = max(alpha_values)
        alpha_mean = sum(alpha_values) / len(alpha_values)

        print(f"   ✓ Alpha interpolated: {len(alpha_interp)} values")
        print(
            f"   Statistics: min={alpha_min:.6f}, max={alpha_max:.6f}, mean={alpha_mean:.6f}"
        )
    except Exception as e:
        print(f"   ⚠ Could not interpolate alpha.water: {e}")

    return interpolated_fields


def demonstrate_surface_dataset(mesh, runTime, surface):
    """
    Demonstrate creating SurfaceDataSet objects.

    Args:
        mesh: OpenFOAM mesh object
        runTime: OpenFOAM Time object
        surface: sampledSurface object

    Returns:
        list: List of created SurfaceDataSet objects
    """
    print(f"\n{'='*60}")
    print("Creating SurfaceDataSet Objects")
    print(f"{'='*60}")

    datasets = []
    adapter = SampledSurfaceAdapter(surface)

    # Create dataset for pressure
    print("\n1. Creating pressure dataset...")
    try:
        p_field = volScalarField.New(runTime, mesh, "p")
        p_dataset = create_interpolated_dataset(
            field_name="pressure",
            field=p_field,
            surface=surface,
            geometry_adapter=adapter,
            mesh=mesh,
            interpolation_scheme="cellPoint",
        )
        datasets.append(p_dataset)
        print(f"   ✓ Pressure dataset created")
        print(f"   Name: {p_dataset.name}")
        print(f"   Field length: {len(p_dataset.field)}")
        print(f"   Geometry type: {type(p_dataset.geometry).__name__}")
    except Exception as e:
        print(f"   ⚠ Could not create pressure dataset: {e}")

    # Create dataset for velocity
    print("\n2. Creating velocity dataset...")
    try:
        U_field = volVectorField.New(runTime, mesh, "U")
        U_dataset = create_interpolated_dataset(
            field_name="velocity",
            field=U_field,
            surface=surface,
            geometry_adapter=adapter,
            mesh=mesh,
            interpolation_scheme="cellPoint",
        )
        datasets.append(U_dataset)
        print(f"   ✓ Velocity dataset created")
        print(f"   Name: {U_dataset.name}")
        print(f"   Field length: {len(U_dataset.field)}")
    except Exception as e:
        print(f"   ⚠ Could not create velocity dataset: {e}")

    return datasets


def demonstrate_geometry_properties(surface):
    """
    Demonstrate accessing surface geometry properties.

    Args:
        surface: sampledSurface object
    """
    print(f"\n{'='*60}")
    print("Surface Geometry Properties")
    print(f"{'='*60}")

    adapter = SampledSurfaceAdapter(surface)

    print(f"\nNumber of points: {len(adapter.points)}")
    print(f"Number of faces: {len(adapter.faces)}")
    print(f"Total surface area: {adapter.total_area:.6e} m²")

    # Calculate some statistics on face areas
    face_area_mags = adapter.face_area_magnitudes
    areas = [float(face_area_mags[i]) for i in range(len(face_area_mags))]

    print(f"\nFace area statistics:")
    print(f"  Min area: {min(areas):.6e} m²")
    print(f"  Max area: {max(areas):.6e} m²")
    print(f"  Mean area: {sum(areas)/len(areas):.6e} m²")


def main():
    """Main function."""
    args = parse_arguments()

    # Check if case exists
    case_path = Path(args.case)
    if not case_path.exists():
        print(f"Error: Case directory not found: {case_path}")
        sys.exit(1)

    # Initialize case
    runTime, mesh = initialize_case(str(case_path))

    # Set time
    set_time(runTime, args.time)

    # Demonstrate surface creation
    surfaces = demonstrate_surface_creation(mesh)

    # Use the plane surface for detailed demonstrations
    if "plane_x" in surfaces:
        plane = surfaces["plane_x"]

        # Demonstrate geometry properties
        demonstrate_geometry_properties(plane)

        # Demonstrate field interpolation
        interpolated_fields = demonstrate_field_interpolation(mesh, runTime, plane)

        # Demonstrate SurfaceDataSet creation
        datasets = demonstrate_surface_dataset(mesh, runTime, plane)

    print(f"\n{'='*60}")
    print("Example Complete!")
    print(f"{'='*60}\n")

    print("\nSummary:")
    print(f"  Created {len(surfaces)} surfaces")
    print(f"  Interpolated fields onto surfaces")
    print(f"  Created SurfaceDataSet objects for further analysis")
    print("\nFor more information, see:")
    print("  - docs/quickstart.rst")
    print("  - docs/api_reference.rst")
    print("  - tests/test_surface_*.py")


if __name__ == "__main__":
    main()
