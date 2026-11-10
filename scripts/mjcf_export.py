"""
Vortexa Studio - MuJoCo MJCF exporter
Produces a minimal but valid MJCF model from Vortexa topology.
"""
from __future__ import annotations
from typing import Sequence, Dict, Any, List
import xml.etree.ElementTree as ET
from xml.dom import minidom


def generate_mjcf(
    topology: Sequence[Dict[str, Any]],
    robot_name: str = "vortexa_robot",
) -> str:
    root = ET.Element("mujoco", model=robot_name)
    ET.SubElement(root, "compiler", angle="radian", coordinate="local")
    ET.SubElement(root, "option", timestep="0.002", gravity="0 0 -9.81")

    default = ET.SubElement(root, "default")
    ET.SubElement(
        default, "joint",
        armature="0.01", damping="0.5", limited="true",
    )
    ET.SubElement(
        default, "geom",
        contype="1", conaffinity="1", friction="1 0.5 0.5",
        rgba="0.6 0.65 0.7 1",
    )

    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "texture", type="skybox", builtin="gradient",
                  rgb1="0.3 0.5 0.7", rgb2="0 0 0", width="512", height="512")
    ET.SubElement(asset, "texture", name="grid", type="2d", builtin="checker",
                  rgb1="0.2 0.2 0.2", rgb2="0.3 0.3 0.3", width="512", height="512")
    ET.SubElement(asset, "material", name="grid", texture="grid",
                  texrepeat="8 8", reflectance="0.1")

    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "geom", name="floor", type="plane", size="3 3 0.05",
                  material="grid")
    ET.SubElement(world, "light", directional="true",
                  pos="0 0 3", dir="0 0 -1", diffuse="0.8 0.8 0.8")

    # Build body chain
    parent_el = world
    for i, link in enumerate(topology):
        name = link.get("name", f"link_{i}")
        length = float(link.get("length", 0.3))
        radius = float(link.get("radius", 0.05))
        mass = float(link.get("mass", 1.0))
        ltype = link.get("type", "revolute")
        axis = (link.get("axis") or "z").lower()
        axis_vec = {"x": "1 0 0", "y": "0 1 0", "z": "0 0 1"}.get(axis, "0 0 1")

        # Position relative to parent: along parent's Z by parent length
        if i == 0:
            pos = "0 0 0"
        else:
            parent_len = float(topology[i - 1].get("length", 0.3))
            pos = f"0 0 {parent_len:.6f}"

        body = ET.SubElement(parent_el, "body", name=name, pos=pos)

        if ltype != "fixed":
            lim = link.get("limit") or {}
            lo = float(lim.get("lower", -3.1416))
            hi = float(lim.get("upper", 3.1416))
            jtype = "slide" if ltype == "prismatic" else "hinge"
            ET.SubElement(
                body, "joint",
                name=f"{name}_joint",
                type=jtype,
                axis=axis_vec,
                range=f"{lo:.5f} {hi:.5f}",
            )

        # Inertial (simple cylinder approximation)
        # Izz ~ 0.5 m r^2, Ixx/Iyy ~ m (3r^2 + h^2)/12
        ixx = mass * (3 * radius**2 + length**2) / 12.0
        izz = 0.5 * mass * radius**2
        ET.SubElement(
            body, "inertial",
            pos=f"0 0 {length/2:.6f}",
            mass=f"{mass:.4f}",
            diaginertia=f"{ixx:.6e} {ixx:.6e} {izz:.6e}",
        )
        ET.SubElement(
            body, "geom",
            name=f"{name}_geom",
            type="cylinder",
            size=f"{radius:.5f} {length/2:.5f}",
            pos=f"0 0 {length/2:.6f}",
        )

        parent_el = body

    # Sensor sites on terminal body
    if parent_el is not world:
        ET.SubElement(parent_el, "site", name="imu", pos="0 0 0", size="0.01")
        ET.SubElement(parent_el, "site", name="tcp", pos="0 0 0.02", size="0.008", rgba="1 0.2 0.2 0.8")

    # Actuators for free joints
    actuator = ET.SubElement(root, "actuator")
    for link in topology:
        if link.get("type") == "fixed":
            continue
        name = link.get("name", "link")
        lim = link.get("limit") or {}
        effort = float(lim.get("effort", 50.0))
        ET.SubElement(
            actuator, "motor",
            name=f"{name}_motor",
            joint=f"{name}_joint",
            gear="1",
            ctrlrange=f"-{effort:.1f} {effort:.1f}",
        )

    rough = ET.tostring(root, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")
