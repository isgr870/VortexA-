"""Minimal URDF → Vortexa topology importer (serial chains)."""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def _f(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default


def parse_urdf(urdf_text: str) -> Dict[str, Any]:
    """Parse URDF XML into a Vortexa topology dict.

    Returns:
      { name, links: [...], message }
    """
    text = (urdf_text or "").strip()
    if not text.startswith("<"):
        raise ValueError("URDF must be XML starting with <robot>")
    root = ET.fromstring(text)
    if root.tag != "robot":
        raise ValueError("Root element must be <robot>")
    robot_name = root.attrib.get("name") or "imported_robot"

    link_map: Dict[str, Dict[str, Any]] = {}
    for link in root.findall("link"):
        name = link.attrib.get("name") or "link"
        mass = 1.0
        inertial = link.find("inertial")
        if inertial is not None:
            m = inertial.find("mass")
            if m is not None:
                mass = _f(m.attrib.get("value"), 1.0)
        length, radius = 0.2, 0.05
        visual = link.find("visual")
        if visual is not None:
            geom = visual.find("geometry")
            if geom is not None:
                cyl = geom.find("cylinder")
                box = geom.find("box")
                sphere = geom.find("sphere")
                if cyl is not None:
                    length = _f(cyl.attrib.get("length"), 0.2)
                    radius = _f(cyl.attrib.get("radius"), 0.05)
                elif box is not None:
                    size = [_f(x) for x in (box.attrib.get("size") or "0.1 0.1 0.2").split()]
                    if len(size) >= 3:
                        length = size[2]
                        radius = max(size[0], size[1]) / 2
                elif sphere is not None:
                    radius = _f(sphere.attrib.get("radius"), 0.05)
                    length = radius * 2
        link_map[name] = {
            "name": name,
            "type": "fixed",
            "length": length,
            "radius": radius,
            "mass": mass,
            "axis": "z",
            "limit": {"lower": -3.14, "upper": 3.14, "effort": 50, "velocity": 2},
        }

    joints = []
    for j in root.findall("joint"):
        jtype = (j.attrib.get("type") or "fixed").lower()
        parent_el = j.find("parent")
        child_el = j.find("child")
        parent = parent_el.attrib.get("link") if parent_el is not None else None
        child = child_el.attrib.get("link") if child_el is not None else None
        axis = "z"
        axis_el = j.find("axis")
        if axis_el is not None:
            xyz = [_f(x) for x in (axis_el.attrib.get("xyz") or "0 0 1").split()]
            if len(xyz) >= 3:
                if abs(xyz[0]) > 0.5:
                    axis = "x"
                elif abs(xyz[1]) > 0.5:
                    axis = "y"
                else:
                    axis = "z"
        lim = {"lower": -3.14, "upper": 3.14, "effort": 50.0, "velocity": 2.0}
        limit_el = j.find("limit")
        if limit_el is not None:
            lim["lower"] = _f(limit_el.attrib.get("lower"), -3.14)
            lim["upper"] = _f(limit_el.attrib.get("upper"), 3.14)
            lim["effort"] = _f(limit_el.attrib.get("effort"), 50)
            lim["velocity"] = _f(limit_el.attrib.get("velocity"), 2)
        joints.append(
            {
                "name": j.attrib.get("name"),
                "type": jtype,
                "parent": parent,
                "child": child,
                "axis": axis,
                "limit": lim,
            }
        )

    children = {j["child"]: j for j in joints if j["child"]}
    roots = [n for n in link_map if n not in children]
    if not roots:
        roots = list(link_map.keys())[:1]
    ordered: List[str] = []
    queue = [roots[0]]
    seen = set()
    while queue:
        n = queue.pop(0)
        if n in seen or n not in link_map:
            continue
        seen.add(n)
        ordered.append(n)
        for j in joints:
            if j["parent"] == n and j["child"]:
                queue.append(j["child"])

    links_out: List[Dict[str, Any]] = []
    for name in ordered:
        L = dict(link_map[name])
        for j in joints:
            if j["child"] == name:
                jt = j["type"]
                L["type"] = jt if jt in ("revolute", "continuous", "prismatic", "fixed") else "revolute"
                L["axis"] = j["axis"]
                L["limit"] = j["limit"]
                break
        else:
            L["type"] = "fixed"
        links_out.append(L)

    if not links_out:
        raise ValueError("No links found in URDF")

    return {
        "name": robot_name,
        "links": links_out,
        "message": f"Imported {robot_name}: {len(links_out)} links (serial approximation)",
    }
