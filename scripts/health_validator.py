"""
Vortexa Studio — sim-ready health validator.
Scores a robot topology for Gazebo / MuJoCo / Isaac readiness.
"""
from __future__ import annotations
from typing import Any, Dict, List, Sequence
import math

DENSITY = {
    "aluminum": 2700.0,
    "carbon": 1600.0,
    "titanium": 4500.0,
    "plastic": 1400.0,
    "steel": 7850.0,
    "abs": 1050.0,
}


def _cylinder_inertia(mass: float, radius: float, length: float) -> Dict[str, float]:
    """Inertia about CoM for solid cylinder along Z."""
    r2 = radius * radius
    h2 = length * length
    ixx = mass * (3 * r2 + h2) / 12.0
    iyy = ixx
    izz = 0.5 * mass * r2
    note = "Structural heuristic only — not a Gazebo/MuJoCo/Isaac certification."
    return {"ixx": ixx, "iyy": iyy, "izz": izz, "ixy": 0.0, "ixz": 0.0, "iyz": 0.0}


def enrich_inertia(topology: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fill missing mass/inertia from geometry + material density."""
    out = []
    for link in topology:
        L = dict(link)
        length = max(0.02, float(L.get("length") or 0.2))
        radius = max(0.005, float(L.get("radius") or 0.04))
        mat = str(L.get("material") or "aluminum").lower()
        dens = DENSITY.get(mat, 2700.0)
        vol = math.pi * radius * radius * length
        if L.get("mass") is None or float(L.get("mass") or 0) <= 0:
            L["mass"] = max(0.01, dens * vol)
        mass = float(L["mass"])
        if not L.get("inertia"):
            L["inertia"] = _cylinder_inertia(mass, radius, length)
        # Default joint limits for movable joints
        if L.get("type") in ("revolute", "continuous", "prismatic") and not L.get("limit"):
            if L.get("type") == "prismatic":
                L["limit"] = {"lower": 0.0, "upper": length, "effort": 80.0, "velocity": 0.5}
            else:
                L["limit"] = {"lower": -3.14159, "upper": 3.14159, "effort": 50.0, "velocity": 2.0}
        # Collision primitive (slightly larger for safety margin)
        if not L.get("collision"):
            L["collision"] = {
                "type": "cylinder",
                "radius": radius * 1.05,
                "length": length * 1.02,
            }
        out.append(L)
    return out


def validate_robot(topology: Sequence[Dict[str, Any]], robot_name: str = "robot") -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    score = 100

    if not topology:
        return {
        "note": note,
            "score": 0,
            "grade": "F",
            "issues": [{"level": "error", "code": "empty", "message": "No parts — add a base and links."}],
            "warnings": [],
            "summary": "Empty robot",
            "ready_for": [],
        }

    names = []
    for i, link in enumerate(topology):
        name = link.get("name") or f"link_{i}"
        if name in names:
            issues.append({"level": "error", "code": "dup_name", "message": f"Duplicate link name: {name}"})
            score -= 15
        names.append(name)

        mass = link.get("mass")
        if mass is None or float(mass) <= 0:
            issues.append({"level": "error", "code": "mass", "message": f"{name}: missing or zero mass"})
            score -= 10
        elif float(mass) > 500:
            warnings.append({"level": "warn", "code": "heavy", "message": f"{name}: mass {mass} kg is unusually high"})
            score -= 2

        if not link.get("inertia") and (mass is None or float(mass or 0) <= 0):
            warnings.append({"level": "warn", "code": "inertia", "message": f"{name}: inertia will be estimated on export"})
            score -= 3

        jtype = link.get("type", "fixed")
        if jtype in ("revolute", "prismatic") and not link.get("limit"):
            warnings.append({"level": "warn", "code": "limits", "message": f"{name}: no joint limits (defaults will be used)"})
            score -= 4

        if jtype not in ("fixed", "revolute", "continuous", "prismatic", None):
            issues.append({"level": "error", "code": "jtype", "message": f"{name}: unknown joint type '{jtype}'"})
            score -= 10

        length = float(link.get("length") or 0)
        radius = float(link.get("radius") or 0)
        if length <= 0 or radius <= 0:
            issues.append({"level": "error", "code": "geom", "message": f"{name}: invalid geometry (length/radius)"})
            score -= 8

    # Tree connectivity: non-root should resolve parent
    root_count = 0
    for i, link in enumerate(topology):
        p = link.get("parent")
        if p is None:
            root_count += 1
            continue
        ok = False
        for j, cand in enumerate(topology):
            if cand.get("id") == p or cand.get("name") == p or j == p:
                ok = True
                break
        if not ok and not (isinstance(p, int) and 0 <= p < len(topology)):
            issues.append({
                "level": "error",
                "code": "parent",
                "message": f"{link.get('name', i)}: parent '{p}' not found",
            })
            score -= 12

    if root_count == 0:
        issues.append({"level": "error", "code": "root", "message": "No root link (parent=null)"})
        score -= 20
    elif root_count > 1:
        warnings.append({"level": "warn", "code": "multi_root", "message": f"{root_count} root links — multi-chain is OK if intentional"})
        score -= 2

    movable = [l for l in topology if l.get("type") not in ("fixed", None)]
    if len(movable) == 0:
        warnings.append({"level": "warn", "code": "static", "message": "No movable joints — static structure only"})
        score -= 5

    score = max(0, min(100, score))
    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    ready = []
    if score >= 60 and not any(i["code"] in ("empty", "root", "dup_name") for i in issues):
        ready.append("URDF")
        ready.append("ROS 2")
    if score >= 70:
        ready.append("MuJoCo")
    if score >= 75:
        ready.append("Isaac / USD")

    summary = f"Grade {grade} ({score}/100) · {len(issues)} issues · {len(warnings)} warnings · {len(topology)} parts · {len(movable)} DoF"
    return {
        "score": score,
        "grade": grade,
        "issues": issues,
        "warnings": warnings,
        "summary": summary,
        "ready_for": ready,
        "part_count": len(topology),
        "dof": len(movable),
        "robot_name": robot_name,
    }
