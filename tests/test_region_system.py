import numpy as np
import pytest
import yaml

from pyOFTools.region_system import Box, Sphere, NotRegion, BinaryRegion, RegionModel, from_dict

def test_box_inside():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    coords = np.array([[0.5, 0.5, 0.5], [1.5, 1.5, 1.5]])
    mask = box.compute(coords)
    assert np.array_equal(mask, [True, False])

def test_sphere_inside():
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    coords = np.array([[0.5, 0, 0], [2.0, 0, 0]])
    mask = sphere.compute(coords)
    assert np.array_equal(mask, [True, False])

def test_not_region():
    sphere = Sphere(type="sphere", center=(0, 0, 0), radius=1.0)
    region = NotRegion(type="not", region=sphere)
    coords = np.array([[0.5, 0, 0], [2.0, 0, 0]])
    mask = region.compute(coords)
    assert np.array_equal(mask, [False, True])

def test_binary_and_region():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.5, 0.5, 0.5), radius=0.2)
    region = BinaryRegion(type="binary", op="and", left=box, right=sphere)
    coords = np.array([
        [0.5, 0.5, 0.5],  # inside both
        [1.5, 0.5, 0.5],  # outside box
        [0.5, 0.5, 0.8],  # inside box but outside sphere
    ])
    mask = region.compute(coords)
    assert np.array_equal(mask, [True, False, False])

def test_operator_overloads_equivalent():
    box = Box(type="box", min=(0, 0, 0), max=(1, 1, 1))
    sphere = Sphere(type="sphere", center=(0.5, 0.5, 0.5), radius=0.2)

    region_manual = BinaryRegion(type="binary", op="and", left=box, right=sphere)
    region_op = box & sphere

    coords = np.array([[0.5, 0.5, 0.5], [2, 2, 2]])
    assert np.array_equal(region_manual.compute(coords), region_op.compute(coords))

def test_yaml_round_trip(tmp_path):
    region = Box(type="box", min=(0, 0, 0), max=(1, 1, 1)) & ~Sphere(
        type="sphere", center=(0.5, 0.5, 0.5), radius=0.25
    )
    coords = np.random.rand(10, 3)
    mask_before = region.compute(coords)

    yaml_file = tmp_path / "region.yaml"
    
    # Convert the model to a dict with proper serialization for YAML
    region_dict = region.model_dump(mode='json')
    
    with open(yaml_file, "w") as f:
        yaml.dump(region_dict, f, default_flow_style=False)

    with open(yaml_file) as f:
        data = yaml.safe_load(f)

    # Use Pydantic's discriminated union to deserialize
    region2 = from_dict(data)
    mask_after = region2.compute(coords)

    assert np.array_equal(mask_before, mask_after)