"""Sim-ready USDA export — hierarchy, mass, collision, joint metadata for Isaac / Omniverse."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional


def export_usd(
    topology: List[Dict[str, Any]],
    robot_name: str = "vortexa_robot",
    out_dir: Optional[Path] = None,
    sensors: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    out_dir = Path(out_dir or Path("urdf"))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{robot_name}.usda"
    links = list(topology or [])
    sensors = sensors or []

    bodies: List[str] = []
    joint_comments: List[str] = []
    for i, link in enumerate(links):
        name = str(link.get("name") or f"link_{i}").replace(" ", "_")
        length = float(link.get("length") or 0.2)
        radius = float(link.get("radius") or 0.05)
        mass = float(link.get("mass") or 1.0)
        ltype = link.get("type") or "revolute"
        axis = (link.get("axis") or "z").lower()
        lim = link.get("limit") or {}
        lo = float(lim.get("lower", -3.14))
        hi = float(lim.get("upper", 3.14))
        effort = float(lim.get("effort", 50.0))
        parent_z = 0.0 if i == 0 else float(links[i - 1].get("length") or 0.2)
        size = max(radius * 2, 0.02)
        scale_z = max(length / size, 0.5)
        half = length / 2.0
        tz = 0.0 if i == 0 else parent_z

        bodies.append(
            f"""
    def Xform "{name}" (
        prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsMassAPI", "PhysicsCollisionAPI"]
    ) {{
        float3 xformOp:translate = (0, 0, {tz:.5f})
        uniform token[] xformOpOrder = ["xformOp:translate"]
        float physics:mass = {mass:.4f}
        def Cube "visual" {{
            float size = {size:.4f}
            float3 xformOp:scale = (1, 1, {scale_z:.4f})
            float3 xformOp:translate = (0, 0, {half:.5f})
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
        }}
        def Cube "collision" (
            prepend apiSchemas = ["PhysicsCollisionAPI"]
        ) {{
            float size = {size:.4f}
            float3 xformOp:scale = (1, 1, {scale_z:.4f})
            float3 xformOp:translate = (0, 0, {half:.5f})
            uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:scale"]
        }}
    }}"""
        )
        if ltype != "fixed":
            joint_comments.append(
                f"# Joint {name}: type={ltype} axis={axis} range=[{lo:.3f},{hi:.3f}] effort={effort:.1f}"
            )

    sensor_blocks: List[str] = []
    for s in sensors:
        sn = str(s.get("name") or "sensor").replace(" ", "_")
        st = s.get("type") or "imu"
        xyz = s.get("xyz") or [0, 0, 0]
        sensor_blocks.append(
            f"""
    def Xform "{sn}" {{
        float3 xformOp:translate = ({float(xyz[0]):.4f}, {float(xyz[1]):.4f}, {float(xyz[2]):.4f})
        uniform token[] xformOpOrder = ["xformOp:translate"]
        custom string sensor:type = "{st}"
    }}"""
        )

    content = f"""#usda 1.0
(
    defaultPrim = "Robot"
    metersPerUnit = 1
    upAxis = "Y"
    doc = "Vortexa Studio v3 sim-ready USD — open in Isaac Sim / Omniverse"
)

def Xform "Robot" (
    kind = "component"
)
{{
    def Xform "base_link"
    {{{''.join(bodies)}{''.join(sensor_blocks)}
    }}
}}

{chr(10).join(joint_comments)}
"""
    path.write_text(content, encoding="utf-8")
    return path
