"""Regression tests for robot health validation."""
from scripts.health_validator import validate_robot


def test_empty_topology_returns_failing_report():
    report = validate_robot([])

    assert report["score"] == 0
    assert report["grade"] == "F"
    assert report["issues"] == [
        {
            "level": "error",
            "code": "empty",
            "message": "No parts — add a base and links.",
        }
    ]
    assert report["warnings"] == []
    assert report["summary"] == "Empty robot"
    assert report["ready_for"] == []


def test_nonempty_topology_preserves_report_contract():
    topology = [
        {
            "id": "base",
            "name": "base",
            "type": "fixed",
            "parent": None,
            "mass": 2.0,
            "length": 0.2,
            "radius": 0.04,
            "inertia": {"ixx": 0.01, "iyy": 0.01, "izz": 0.01},
        }
    ]

    report = validate_robot(topology, robot_name="regression_robot")

    assert report["robot_name"] == "regression_robot"
    assert report["part_count"] == 1
    assert report["dof"] == 0
    assert report["score"] == 95
    assert report["grade"] == "A"
    assert "URDF" in report["ready_for"]
    assert "MuJoCo" in report["ready_for"]
    assert "Isaac / USD" in report["ready_for"]
