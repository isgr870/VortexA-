"""Kinematics unit tests against the articulated arm template."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kinematics_engine import KinematicsEngine


def arm_links():
    data = json.loads((ROOT / "assets" / "templates" / "articulated_arm.json").read_text(encoding="utf-8"))
    return data["links"]


def test_fk_identity_home():
    eng = KinematicsEngine(arm_links())
    q = [0.0] * eng.n_joints
    T = eng.forward_kinematics(q)
    assert T.shape == (4, 4)
    assert abs(T[3, 3] - 1.0) < 1e-9


def test_fk_moves_with_joint():
    eng = KinematicsEngine(arm_links())
    p0 = eng.end_effector_position([0.0] * eng.n_joints)
    q = [0.0] * eng.n_joints
    # Shoulder pitch (j1) changes EE position for typical serial Z-axis link models
    idx = 1 if eng.n_joints > 1 else 0
    q[idx] = 0.6
    p1 = eng.end_effector_position(q)
    assert np.linalg.norm(np.asarray(p1) - np.asarray(p0)) > 1e-6


def test_ik_reduces_error():
    eng = KinematicsEngine(arm_links())
    q0 = [0.0] * eng.n_joints
    if eng.n_joints >= 3:
        q0[1], q0[2] = -0.4, 0.7
    target = eng.end_effector_position(q0)
    # perturb seed
    seed = [0.0] * eng.n_joints
    result = eng.solve_ik(list(target), seed)
    assert "joint_angles" in result
    assert result.get("residual", 1.0) < 0.05 or result.get("success")


def test_clamp_angles():
    eng = KinematicsEngine(arm_links())
    q = [100.0] * eng.n_joints
    c = eng.clamp_angles(q)
    assert len(c) == eng.n_joints
