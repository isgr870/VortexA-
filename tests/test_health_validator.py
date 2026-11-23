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


def test_enrichment_provenance_distinguishes_preserved_and_generated_fields():
    from scripts.health_validator import enrich_topology_with_provenance

    topology = [
        {
            "id": "base",
            "name": "base",
            "type": "fixed",
            "parent": None,
            "mass": 8.0,
            "inertia": {"ixx": 1.0, "iyy": 1.0, "izz": 1.0},
            "collision": {"type": "box", "size": [1.0, 1.0, 1.0]},
        },
        {
            "id": "joint_1",
            "name": "joint_1",
            "type": "revolute",
            "parent": "base",
            "length": 0.2,
            "radius": 0.04,
        },
    ]

    enriched, provenance = enrich_topology_with_provenance(topology)

    assert enriched[0]["mass"] == 8.0
    assert enriched[0]["inertia"] == topology[0]["inertia"]
    assert enriched[0]["collision"] == topology[0]["collision"]

    assert provenance[0]["mass"] == "present_in_input"
    assert provenance[0]["inertia"] == "present_in_input"
    assert provenance[0]["collision"] == "present_in_input"

    assert provenance[1]["mass"] == "estimated"
    assert provenance[1]["inertia"] == "estimated"
    assert provenance[1]["limit"] == "defaulted"
    assert provenance[1]["collision"] == "generated"


def test_enrichment_provenance_does_not_modify_input_topology():
    from scripts.health_validator import enrich_topology_with_provenance

    topology = [{
        "id": "joint_1",
        "name": "joint_1",
        "type": "prismatic",
        "parent": None,
        "length": 0.3,
        "radius": 0.05,
    }]
    original = [dict(link) for link in topology]

    enriched, provenance = enrich_topology_with_provenance(topology)

    assert topology == original
    assert enriched is not topology
    assert enriched[0] is not topology[0]
    assert provenance[0]["limit"] == "defaulted"
