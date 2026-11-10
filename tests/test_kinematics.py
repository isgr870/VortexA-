#!/usr/bin/env python3
"""Golden and unit tests for the kinematics engine."""

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kinematics_engine import KinematicsEngine
import json


def load_arm():
    with open(ROOT / "assets" / "templates" / "articulated_arm.json") as f:
        data = json.load(f)
    return data["links"]


def test_fk_zero_pose():
    topo = load_arm()
    eng = KinematicsEngine(topo)
    T = eng.forward_kinematics([0.0] * 6)
    pos = T[:3, 3]
    # At zero angles the arm should reach roughly the sum of link lengths in z
    # (exact value depends on the topology definition)
    assert pos[0] == 0.0 or abs(pos[0]) < 1e-6
    assert np.linalg.norm(pos) > 0.5  # must reach somewhere
    print("PASS: test_fk_zero_pose", pos)


def test_fk_deterministic():
    topo = load_arm()
    eng = KinematicsEngine(topo)
    angles = [0.1, -0.3, 0.5, 0.0, 0.2, -0.1]
    assert eng.validate_fk_consistency(angles)
    print("PASS: test_fk_deterministic")


def test_ik_reaches_target():
    topo = load_arm()
    eng = KinematicsEngine(topo)
    # First get a reachable point via FK
    seed = [0.2, -0.4, 0.6, 0.1, 0.3, 0.0]
    target = eng.end_effector_position(seed)
    # Solve IK back to it
    solved = eng.solve_ik(target, initial_angles=[0.0] * 6, max_iters=80)
    reached = eng.end_effector_position(solved)
    err = np.linalg.norm(reached - target)
    print(f"  IK residual: {err:.6f}")
    assert err < 0.05, f"IK residual too large: {err}"
    print("PASS: test_ik_reaches_target")


def test_urdf_generation():
    from scripts.urdf_generator_api import generate_urdf
    topo = load_arm()
    urdf = generate_urdf(topo, robot_name="test_arm")
    assert '<?xml version="1.0"?>' in urdf
    assert '<robot name="test_arm">' in urdf
    assert "</robot>" in urdf
    assert urdf.count("<link ") >= 6
    assert urdf.count("<joint ") >= 5
    assert "<inertial>" in urdf
    assert "<axis " in urdf
    print("PASS: test_urdf_generation")
    # Write for manual inspection
    out = ROOT / "urdf" / "test_arm.urdf"
    out.parent.mkdir(exist_ok=True)
    out.write_text(urdf)
    print(f"  Wrote {out}")


if __name__ == "__main__":
    test_fk_zero_pose()
    test_fk_deterministic()
    test_ik_reaches_target()
    test_urdf_generation()
    print("\nAll kinematics tests passed.")
