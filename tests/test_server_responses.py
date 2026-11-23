"""Tests for server action response contracts."""

from server import _build_enrichment_response, _build_validation_response


def sample_topology():
    return [
        {
            "id": "base", "name": "base", "type": "fixed",
            "parent": None, "mass": 8.0, "length": 0.2, "radius": 0.04,
            "inertia": {"ixx": 1.0, "iyy": 1.0, "izz": 1.0},
            "collision": {"type": "box", "size": [1.0, 1.0, 1.0]},
        },
        {
            "id": "joint_1", "name": "joint_1", "type": "revolute",
            "parent": "base", "length": 0.2, "radius": 0.04,
        },
    ]


def test_validation_response_includes_aligned_provenance():
    topology = sample_topology()
    response = _build_validation_response(topology, "response_test")

    assert response["status"] == "success"
    assert response["action"] == "validate_robot"
    assert response["report"]["robot_name"] == "response_test"
    assert len(response["enriched_topology"]) == len(topology)
    assert len(response["field_provenance"]) == len(topology)
    assert response["field_provenance"][0]["mass"] == "present_in_input"
    assert response["field_provenance"][1]["mass"] == "estimated"
    assert response["field_provenance"][1]["inertia"] == "estimated"
    assert response["field_provenance"][1]["limit"] == "defaulted"
    assert response["field_provenance"][1]["collision"] == "generated"
    assert topology[1].get("mass") is None


def test_enrichment_response_preserves_contract_and_adds_provenance():
    topology = sample_topology()
    response = _build_enrichment_response(topology)

    assert response["status"] == "success"
    assert response["action"] == "enrich_physics"
    assert len(response["topology"]) == len(topology)
    assert len(response["field_provenance"]) == len(topology)
    assert response["topology"][0]["mass"] == 8.0
    assert response["field_provenance"][0]["mass"] == "present_in_input"
    assert response["field_provenance"][1]["mass"] == "estimated"
    assert topology[1].get("mass") is None
    assert "2 parts" in response["message"]


def test_empty_topology_returns_empty_provenance():
    validation = _build_validation_response([])
    enrichment = _build_enrichment_response([])

    assert validation["status"] == "success"
    assert validation["report"]["score"] == 0
    assert validation["enriched_topology"] == []
    assert validation["field_provenance"] == []
    assert enrichment["status"] == "success"
    assert enrichment["topology"] == []
    assert enrichment["field_provenance"] == []
