#!/usr/bin/env python3
"""
Vortexa Studio v3 - Core Asynchronous WebSocket Bridge
Industry-grade local computation server for offline robotics design.
"""

import asyncio
import json
import numpy as np
import logging
import os
import re
import sys
from pathlib import Path

import websockets
try:
    from websockets.asyncio.server import serve
except ImportError:
    from websockets.server import serve  # older websockets

# Ensure scripts are importable
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.kinematics_engine import KinematicsEngine
from scripts.rigidbody_dynamics import RigidBodyDynamics
from scripts.urdf_generator_api import generate_urdf
from scripts.pybullet_sim import generate_pybullet_script
from scripts.ros2_export import generate_ros2_package
from scripts.mjcf_export import generate_mjcf
from scripts.usd_export import export_usd
from scripts.health_validator import validate_robot, enrich_inertia
from scripts.urdf_import import parse_urdf
from scripts.security import safe_name, safe_template_name, resolve_under

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("VortexaBridge")

def _read_version() -> str:
    try:
        return (ROOT / "VERSION").read_text(encoding="utf-8").strip() or "3.6.0"
    except Exception:
        return "3.6.0"

APP_VERSION = _read_version()
SESSION_TOKEN = os.environ.get("VORTEXA_TOKEN", "").strip()
ALLOWED_ORIGINS = {
    o.strip()
    for o in os.environ.get(
        "VORTEXA_ALLOWED_ORIGINS",
        "http://127.0.0.1:8080,http://localhost:8080,http://127.0.0.1:8080/,http://localhost:8080/",
    ).split(",")
    if o.strip()
}
# Empty token = generate ephemeral on start (printed once)
import secrets as _secrets
if not SESSION_TOKEN:
    SESSION_TOKEN = _secrets.token_urlsafe(24)


TEMPLATES_DIR = ROOT / "assets" / "templates"
KIT_DIR = ROOT / "assets" / "kit"
URDF_DIR = ROOT / "urdf"
CONFIG_DIR = ROOT / "config"

# Ensure directories exist
for d in (TEMPLATES_DIR, URDF_DIR, CONFIG_DIR):
    d.mkdir(parents=True, exist_ok=True)


def load_template(template_name: str) -> dict:
    """Load a robot topology template with fallback."""
    candidates = [
        TEMPLATES_DIR / f"{template_name}.json",
        TEMPLATES_DIR / "articulated_arm.json",
    ]
    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded template: %s", path.name)
            return data
    raise FileNotFoundError(f"No template found for '{template_name}'")


async def handle_client(websocket):
    client = websocket.remote_address
    origin = None
    try:
        origin = websocket.request.headers.get("Origin") if hasattr(websocket, "request") else None
    except Exception:
        origin = None
    # websockets v10+ may expose origin differently
    if origin is None:
        try:
            origin = dict(getattr(websocket, "request_headers", {}) or {}).get("Origin")
        except Exception:
            pass
    if origin and ALLOWED_ORIGINS and origin.rstrip("/") not in {o.rstrip("/") for o in ALLOWED_ORIGINS}:
        # Allow missing Origin for non-browser clients (Termux tools); block bad browser origins
        if origin.startswith("http://") or origin.startswith("https://"):
            logger.warning("Rejected Origin %s from %s", origin, client)
            await websocket.close(code=1008, reason="origin not allowed")
            return
    logger.info("Client connected: %s origin=%s", client, origin)

    try:
        async for raw in websocket:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON payload"
                }))
                continue

            action = data.get("action")
            # Token gate for mutating / export / filesystem actions
            protected = {
                "compile_urdf", "export_ros2", "export_mjcf", "export_usd",
                "export_trajectory", "export_trajectory_csv", "save_project",
                "load_project", "motion_save", "import_urdf", "export_pybullet",
            }
            if action in protected and SESSION_TOKEN:
                token = data.get("token") or data.get("auth_token") or ""
                if token != SESSION_TOKEN:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "action": action,
                        "message": "Unauthorized — open UI from local Vortexa server (session token required for exports).",
                    }))
                    continue
            logger.info("Action: %s", action)

            try:
                if action == "load_template":
                    template_name = safe_template_name(data.get("template_name", "articulated_arm"))
                    template = load_template(template_name)
                    chain_name = data.get("chain") or template.get("default_chain")
                    chains = template.get("chains")
                    if chains and chain_name and chain_name in chains:
                        body_key = "torso" if "torso" in chains else ("body" if "body" in chains else None)
                        topo = []
                        if body_key and chain_name != body_key:
                            topo = list(chains[body_key])
                        topo = topo + list(chains[chain_name])
                    else:
                        topo = template.get("links", [])
                    response = {
                        "status": "success",
                        "action": "load_template",
                        "template_name": template.get("name", template_name),
                        "topology": topo,
                        "multi_chain": bool(template.get("multi_chain")),
                        "chains": list((chains or {}).keys()),
                        "all_chains": chains,
                        "chain_origins": template.get("chain_origins") or {},
                        "active_chain": chain_name,
                        "default_target": template.get("default_target"),
                        "reach_m": template.get("reach_m"),
                        "tcp_offset": template.get("tcp_offset") or {"xyz": [0, 0, 0], "rpy": [0, 0, 0]},
                        "metadata": {
                            "dof": len([l for l in topo if l.get("type") != "fixed"]),
                            "link_count": len(topo),
                            "category": template.get("category"),
                            "total_dof": template.get("dof"),
                        }
                    }

                elif action == "select_chain":
                    template_name = data.get("template_name") or data.get("robot")
                    chain_name = data.get("chain")
                    template = load_template(template_name) if template_name else None
                    if not template or not template.get("chains"):
                        response = {"status": "error", "action": "select_chain", "message": "No multi-chain robot loaded."}
                    else:
                        chains = template["chains"]
                        if chain_name not in chains:
                            response = {"status": "error", "action": "select_chain", "message": f"Unknown chain: {chain_name}"}
                        else:
                            body_key = "torso" if "torso" in chains else ("body" if "body" in chains else None)
                            topo = list(chains[body_key]) if body_key and chain_name != body_key else []
                            topo = topo + list(chains[chain_name])
                            response = {
                                "status": "success",
                                "action": "select_chain",
                                "active_chain": chain_name,
                                "topology": topo,
                                "chains": list(chains.keys()),
                                "all_chains": chains,
                                "chain_origins": template.get("chain_origins") or {},
                                "template_name": template.get("name"),
                            }

                elif action == "compute_fk":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    joint_angles = data.get("joint_angles", [0.0] * 6)
                    engine = KinematicsEngine(topology)
                    tcp = data.get("tcp_offset") or {}
                    engine.set_tcp_offset(tcp.get("xyz"), tcp.get("rpy"))
                    angles = engine.clamp_angles(joint_angles)
                    use_tcp = any(abs(v) > 1e-9 for v in getattr(engine, "tcp_xyz", [0, 0, 0]))
                    pose = engine.forward_kinematics_tcp(angles) if use_tcp else engine.forward_kinematics(angles)
                    sing = engine.singularity_index(angles)
                    response = {
                        "status": "success",
                        "action": "compute_fk",
                        "end_effector_position": pose[:3, 3].tolist(),
                        "transformation_matrix": pose.tolist(),
                        "joint_angles": angles.tolist(),
                        "manipulability": sing["manipulability"],
                        "sigma_min": sing["sigma_min"],
                        "near_singularity": sing["near_singularity"],
                        "max_reach": engine.max_reach(),
                        "tcp_applied": use_tcp,
                    }

                elif action == "compute_ik":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    target = data.get("target", [0.5, 0.0, 0.8])
                    initial = data.get("initial_angles") or data.get("joint_angles")
                    engine = KinematicsEngine(topology)
                    tcp = data.get("tcp_offset") or {}
                    engine.set_tcp_offset(tcp.get("xyz"), tcp.get("rpy"))
                    result = engine.solve_ik(target, initial)
                    response = {
                        "status": "success" if result.get("success") else "partial",
                        "action": "compute_ik",
                        "joint_angles": result["joint_angles"],
                        "target": target,
                        "residual": result["residual"],
                        "manipulability": result["manipulability"],
                        "sigma_min": result.get("sigma_min"),
                        "near_singularity": result.get("near_singularity"),
                        "iterations": result["iterations"],
                        "end_effector_position": result.get("end_effector_position"),
                        "success": result["success"],
                        "tcp_applied": any(abs(v) > 1e-9 for v in getattr(engine, "tcp_xyz", [0,0,0])),
                    }

                elif action == "compute_dynamics":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    joint_angles = data.get("joint_angles", [0.0] * 6)
                    dyn = RigidBodyDynamics(topology)
                    mass_matrix = dyn.compute_mass_matrix(joint_angles)
                    response = {
                        "status": "success",
                        "action": "compute_dynamics",
                        "mass_matrix": mass_matrix,
                    }

                elif action == "compile_urdf":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    robot_name = safe_name(data.get("robot_name", "vortexa_robot"), "vortexa_robot")
                    urdf_str = generate_urdf(topology, robot_name=robot_name)
                    out_path = resolve_under(URDF_DIR, f"{robot_name}.urdf")
                    out_path.write_text(urdf_str, encoding="utf-8")
                    response = {
                        "status": "success",
                        "action": "compile_urdf",
                        "urdf": urdf_str,
                        "path": str(out_path),
                    }

                elif action == "export_pybullet":
                    urdf_filename = data.get("urdf_filename", "vortexa_robot.urdf")
                    script = generate_pybullet_script(urdf_filename)
                    response = {
                        "status": "success",
                        "action": "export_pybullet",
                        "script": script,
                    }

                elif action == "export_ros2":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    robot_name = safe_name(data.get("robot_name", "vortexa_robot"), "vortexa_robot")
                    files = generate_ros2_package(topology, robot_name=robot_name)
                    response = {
                        "status": "success",
                        "action": "export_ros2",
                        "package_name": f"{robot_name}_description",
                        "files": files,
                    }

                elif action == "export_mjcf":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    robot_name = safe_name(data.get("robot_name", "vortexa_robot"), "vortexa_robot")
                    mjcf = generate_mjcf(topology, robot_name=robot_name)
                    out = resolve_under(URDF_DIR, f"{robot_name}.xml")
                    out.write_text(mjcf, encoding="utf-8")
                    response = {
                        "status": "success",
                        "action": "export_mjcf",
                        "mjcf": mjcf,
                        "path": str(out),
                    }

                elif action == "plan_cartesian":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    start = data.get("start")  # joint angles
                    goal = data.get("goal") or data.get("target") or [0.4, 0.0, 0.55]
                    waypoints = int(data.get("waypoints", 12))
                    waypoints = max(2, min(waypoints, 50))
                    engine = KinematicsEngine(topology)
                    if start is None:
                        start = [0.0] * engine.n_joints
                    # FK start position
                    p0 = engine.end_effector_position(start)
                    p1 = __import__("numpy").array(goal, dtype=float)
                    path_joints = []
                    path_pos = []
                    angles = list(start)
                    for k in range(waypoints):
                        t = k / (waypoints - 1)
                        target = (1 - t) * p0 + t * p1
                        result = engine.solve_ik(target.tolist(), angles)
                        angles = result["joint_angles"]
                        path_joints.append(angles)
                        path_pos.append(result.get("end_effector_position") or target.tolist())
                    response = {
                        "status": "success",
                        "action": "plan_cartesian",
                        "joint_path": path_joints,
                        "cartesian_path": path_pos,
                        "waypoints": waypoints,
                        "final_residual": result["residual"],
                        "success": result["success"],
                    }

                elif action == "export_trajectory":
                    # Joint timeseries CSV (ROS bag-friendly columns)
                    path = data.get("joint_path") or []
                    dt = float(data.get("dt") or 0.05)
                    name = safe_name(data.get("robot_name") or "vortexa_traj", "vortexa_traj")
                    out_dir = ROOT / "urdf"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    csv_path = resolve_under(out_dir, f"{name}_trajectory.csv")
                    lines = ["time," + ",".join(f"j{i}" for i in range(len(path[0]) if path else []))]
                    for k, row in enumerate(path):
                        lines.append(f"{k*dt:.4f}," + ",".join(f"{float(v):.6f}" for v in row))
                    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    response = {
                        "status": "success",
                        "action": "export_trajectory",
                        "path": str(csv_path),
                        "waypoints": len(path),
                        "dt": dt,
                        "message": f"Trajectory CSV written ({len(path)} steps @ {dt}s).",
                    }

                elif action == "list_presets":
                    template_name = data.get("template_name") or data.get("robot") or "articulated_arm"
                    presets_path = ROOT / "assets" / "kit" / "presets" / "poses.json"
                    catalog = json.loads(presets_path.read_text(encoding="utf-8")) if presets_path.exists() else {"presets": {}, "by_template": {}}
                    by = (
                        catalog.get("by_template", {}).get(template_name)
                        or catalog.get("by_template", {}).get("blank")
                        or catalog.get("by_template", {}).get("articulated_arm")
                        or {}
                    )
                    response = {
                        "status": "success",
                        "action": "list_presets",
                        "template_name": template_name,
                        "available": list(by.keys()),
                        "labels": {k: catalog.get("presets", {}).get(k, {}).get("label", k) for k in by.keys()},
                        "poses": by,
                    }

                elif action == "apply_preset":
                    template_name = data.get("template_name") or "articulated_arm"
                    preset = data.get("preset") or "home"
                    topology = data.get("topology") or []
                    if not topology and template_name not in ("blank", "custom"):
                        try:
                            topology = load_template(template_name).get("links", [])
                        except Exception:
                            topology = []
                    presets_path = ROOT / "assets" / "kit" / "presets" / "poses.json"
                    catalog = json.loads(presets_path.read_text(encoding="utf-8")) if presets_path.exists() else {"by_template": {}}
                    by = (
                        catalog.get("by_template", {}).get(template_name)
                        or catalog.get("by_template", {}).get("blank")
                        or {}
                    )
                    angles = by.get(preset)
                    n = len([l for l in topology if l.get("type") != "fixed"])
                    if angles is None:
                        angles = [0.0] * n
                        preset = "home"
                    else:
                        angles = list(angles) + [0.0] * max(0, n - len(angles))
                        angles = angles[:n]
                    engine = KinematicsEngine(topology) if topology else None
                    if engine:
                        angles = engine.clamp_angles(angles).tolist()
                        sing = engine.singularity_index(angles)
                        ee = engine.end_effector_position(angles).tolist()
                    else:
                        angles = [float(a) for a in angles]
                        sing = {"manipulability": 0.0, "near_singularity": False}
                        ee = [0.0, 0.0, 0.0]
                    response = {
                        "status": "success",
                        "action": "apply_preset",
                        "preset": preset,
                        "joint_angles": angles,
                        "end_effector_position": ee,
                        "manipulability": sing["manipulability"],
                        "near_singularity": sing["near_singularity"],
                    }

                elif action == "export_usd":
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    name = data.get("robot_name") or "vortexa_robot"
                    try:
                        path = export_usd(topology, robot_name=name, out_dir=ROOT / "urdf")
                        response = {
                            "status": "success",
                            "action": "export_usd",
                            "path": str(path),
                            "message": f"USD ASCII written to {path.name}. Open in Isaac Sim / Omniverse.",
                        }
                    except Exception as e:
                        logger.exception("USD export failed")
                        response = {
                            "status": "error",
                            "action": "export_usd",
                            "message": f"USD export failed: {e}",
                        }

                elif action == "collision_check":
                    topology = data.get("topology") or []
                    joint_angles = data.get("joint_angles") or []
                    # Simple sphere-sweep self-collision heuristic along serial chain
                    engine = KinematicsEngine(topology)
                    angles = engine.clamp_angles(joint_angles)
                    # Accumulate link midpoints via partial FK
                    spheres = []
                    # approximate: EE and intermediate by sequential
                    T = np.eye(4)
                    active = [l for l in topology if l.get("type") != "fixed"]
                    ai = 0
                    for link in topology:
                        length = float(link.get("length") or 0.2)
                        radius = float(link.get("radius") or 0.05) * 1.1
                        # mid of link in current frame
                        mid = T @ np.array([0, 0, length/2, 1.0])
                        spheres.append({"name": link.get("name"), "center": mid[:3].tolist(), "radius": radius})
                        # advance
                        from scripts.kinematics_engine import KinematicsEngine as KE
                        # use engine internal step if possible — fallback translate along z
                        ct = np.eye(4)
                        ct[2, 3] = length
                        if link.get("type") != "fixed" and ai < len(angles):
                            # rotation applied at joint before link extent — simplified
                            pass
                        T = T @ ct
                        if link.get("type") != "fixed":
                            ai += 1
                    collisions = []
                    for i in range(len(spheres)):
                        for j in range(i+2, len(spheres)):  # skip adjacent
                            a, b = spheres[i], spheres[j]
                            d = sum((a["center"][k]-b["center"][k])**2 for k in range(3))**0.5
                            if d < (a["radius"] + b["radius"]) * 0.85:
                                collisions.append({"a": a["name"], "b": b["name"], "distance": d})
                    response = {
                        "status": "success",
                        "action": "collision_check",
                        "experimental": True,
                        "disclaimer": "Sphere heuristic along chain axis — not pose-complete; do not use for safety decisions.",
                        "spheres": spheres,
                        "collisions": collisions,
                        "has_collision": len(collisions) > 0,
                        "message": ("Self-collision risk: " + ", ".join(f'{c["a"]}/{c["b"]}' for c in collisions)) if collisions else "No self-collision detected (sphere heuristic).",
                    }

                elif action == "kit_catalog":
                    catalog_path = KIT_DIR / "catalog.json"
                    if catalog_path.exists():
                        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                    else:
                        catalog = {"name": "TexaKit", "categories": {}, "end_effectors": []}
                    templates_meta = []
                    for tp in sorted(TEMPLATES_DIR.glob("*.json")):
                        try:
                            t = json.loads(tp.read_text(encoding="utf-8"))
                            templates_meta.append({
                                "id": tp.stem,
                                "name": t.get("name", tp.stem),
                                "description": t.get("description", ""),
                                "category": t.get("category", "manipulator"),
                                "dof": t.get("dof", len([l for l in t.get("links", []) if l.get("type") != "fixed"])),
                                "reach_m": t.get("reach_m"),
                            })
                        except Exception:
                            templates_meta.append({"id": tp.stem, "name": tp.stem})
                    response = {
                        "status": "success",
                        "action": "kit_catalog",
                        "catalog": catalog,
                        "templates": templates_meta,
                    }

                elif action == "command":
                    # Command & control of current robot
                    cmd = (data.get("command") or "hold").lower()
                    topology = data.get("topology") or load_template("articulated_arm")["links"]
                    joint_angles = data.get("joint_angles") or [0.0] * max(1, len([l for l in topology if l.get("type") != "fixed"]))
                    engine = KinematicsEngine(topology)
                    angles = engine.clamp_angles(joint_angles)

                    if cmd == "home":
                        n = engine.n_joints
                        home = [0.0] * n
                        if n >= 6:
                            home[1] = -0.6
                            home[2] = 1.0
                            if n > 4:
                                home[4] = 0.3
                        elif n >= 3:
                            home[1] = -0.4
                            home[2] = 0.8
                        angles = engine.clamp_angles(home)
                        pose = engine.end_effector_position(angles)
                        response = {
                            "status": "success", "action": "command", "command": "home",
                            "joint_angles": [float(a) for a in angles],
                            "end_effector_position": pose.tolist(),
                            "message": "Moved to home pose.",
                        }
                    elif cmd == "stow":
                        n = engine.n_joints
                        stow = [0.0] * n
                        if n >= 3:
                            stow[1] = 0.3
                            stow[2] = -1.2
                        angles = engine.clamp_angles(stow)
                        pose = engine.end_effector_position(angles)
                        response = {
                            "status": "success", "action": "command", "command": "stow",
                            "joint_angles": [float(a) for a in angles],
                            "end_effector_position": pose.tolist(),
                            "message": "Stowed for transport / safe pose.",
                        }
                    elif cmd == "jog":
                        # Cartesian jog by delta meters in world frame
                        delta = data.get("delta") or [0.02, 0, 0]
                        current = engine.end_effector_position(angles)
                        target = (current + __import__("numpy").array(delta, dtype=float)).tolist()
                        result = engine.solve_ik(target, angles)
                        response = {
                            "status": "success", "action": "command", "command": "jog",
                            "joint_angles": result["joint_angles"],
                            "end_effector_position": result.get("end_effector_position"),
                            "residual": result.get("residual"),
                            "success": result.get("success"),
                            "message": "Cartesian jog applied." if result.get("success") else "Jog limited by workspace.",
                        }
                    elif cmd == "hold":
                        pose = engine.end_effector_position(angles)
                        response = {
                            "status": "success", "action": "command", "command": "hold",
                            "joint_angles": [float(a) for a in angles],
                            "end_effector_position": pose.tolist(),
                            "message": "Holding current pose.",
                        }
                    else:
                        response = {
                            "status": "error", "action": "command",
                            "message": f"Unknown command: {cmd}. Use home|stow|jog|hold.",
                        }


                elif action == "import_urdf":
                    urdf_xml = data.get("urdf") or data.get("xml") or ""
                    try:
                        parsed = parse_urdf(urdf_xml)
                        response = {
                            "status": "success",
                            "action": "import_urdf",
                            "topology": parsed["links"],
                            "robot_name": parsed["name"],
                            "message": parsed["message"],
                        }
                    except Exception as e:
                        logger.exception("URDF import failed")
                        response = {
                            "status": "error",
                            "action": "import_urdf",
                            "message": f"Import failed: {e}",
                        }

                elif action == "motion_save":
                    # Persist named motion sequence (targets list) under urdf/motions
                    name = re.sub(r"[^a-zA-Z0-9_\-]", "_", data.get("name") or "sequence")
                    waypoints = data.get("waypoints") or []
                    mdir = ROOT / "urdf" / "motions"
                    mdir.mkdir(parents=True, exist_ok=True)
                    mpath = mdir / f"{name}.json"
                    payload = {
                        "name": name,
                        "waypoints": waypoints,
                        "template": data.get("template"),
                        "active_chain": data.get("active_chain"),
                    }
                    mpath.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    response = {
                        "status": "success",
                        "action": "motion_save",
                        "path": str(mpath),
                        "message": f"Motion '{name}' saved ({len(waypoints)} waypoints).",
                    }

                elif action == "motion_list":
                    mdir = ROOT / "urdf" / "motions"
                    items = []
                    if mdir.exists():
                        for p in sorted(mdir.glob("*.json")):
                            try:
                                d = json.loads(p.read_text(encoding="utf-8"))
                                items.append({"name": d.get("name") or p.stem, "waypoints": len(d.get("waypoints") or [])})
                            except Exception:
                                items.append({"name": p.stem, "waypoints": 0})
                    response = {
                        "status": "success",
                        "action": "motion_list",
                        "motions": items,
                        "message": f"{len(items)} saved motions.",
                    }

                elif action == "health":
                    response = {
                        "status": "success",
                        "action": "health",
                        "version": APP_VERSION,
                        "token": SESSION_TOKEN,
                        "product_stage": "early_design_studio",
                        "texakit": "3.1",
                        "templates": [p.stem for p in TEMPLATES_DIR.glob("*.json")],
                    }

                elif action == "validate_robot":
                    topology = data.get("topology") or []
                    name = data.get("robot_name") or "vortexa_robot"
                    enriched = enrich_inertia(topology)
                    report = validate_robot(enriched, robot_name=name)
                    response = {
                        "status": "success",
                        "action": "validate_robot",
                        "report": report,
                        "enriched_topology": enriched,
                        "message": report.get("summary", "Validation complete"),
                    }

                elif action == "enrich_physics":
                    topology = data.get("topology") or []
                    enriched = enrich_inertia(topology)
                    response = {
                        "status": "success",
                        "action": "enrich_physics",
                        "topology": enriched,
                        "message": f"Physics enriched for {len(enriched)} parts (mass, inertia, limits, collision).",
                    }

                
                elif action == "export_trajectory_csv":
                    import csv, time
                    waypoints = data.get("waypoints") or []
                    angles = data.get("joint_angles") or []
                    rows = []
                    if waypoints:
                        for i, wp in enumerate(waypoints):
                            j = wp.get("joints") if isinstance(wp, dict) else wp
                            if j:
                                rows.append([i * 0.1] + [float(x) for x in j])
                    elif angles:
                        rows.append([0.0] + [float(x) for x in angles])
                    out = ROOT / "urdf"
                    out.mkdir(parents=True, exist_ok=True)
                    path = out / f"traj_{int(time.time())}.csv"
                    with open(path, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        if rows:
                            n = max(0, len(rows[0]) - 1)
                            w.writerow(["t"] + [f"j{k}" for k in range(n)])
                            w.writerows(rows)
                    response = {
                        "status": "success",
                        "action": "export_trajectory_csv",
                        "path": str(path),
                        "message": f"Wrote {len(rows)} rows → {path.name}",
                    }

                elif action == "save_project":
                    project = {
                        "format": "vortexa_project",
                        "version": "3.5",
                        "name": data.get("name") or "untitled",
                        "template": data.get("template"),
                        "topology": data.get("topology") or [],
                        "joint_angles": data.get("joint_angles") or [],
                        "active_chain": data.get("active_chain"),
                        "tcp": data.get("tcp"),
                        "motions": data.get("motions") or [],
                        "scene": data.get("scene") or [],
                        "notes": data.get("notes") or "",
                    }
                    out = ROOT / "projects"
                    out.mkdir(parents=True, exist_ok=True)
                    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in project["name"])[:64]
                    path = out / f"{safe}.vortexa.json"
                    path.write_text(json.dumps(project, indent=2), encoding="utf-8")
                    response = {
                        "status": "success",
                        "action": "save_project",
                        "path": str(path),
                        "message": f"Project saved: {path.name}",
                    }

                elif action == "list_projects":
                    pdir = ROOT / "projects"
                    pdir.mkdir(parents=True, exist_ok=True)
                    items = []
                    for p in sorted(pdir.glob("*.vortexa.json")):
                        try:
                            meta = json.loads(p.read_text(encoding="utf-8"))
                            items.append({"name": meta.get("name", p.stem), "file": p.name, "parts": len(meta.get("topology") or [])})
                        except Exception:
                            items.append({"name": p.stem, "file": p.name, "parts": 0})
                    # also list bundled examples
                    ex = ROOT / "assets" / "examples"
                    examples = []
                    if ex.exists():
                        for p in sorted(ex.glob("*.vortexa.json")):
                            try:
                                meta = json.loads(p.read_text(encoding="utf-8"))
                                examples.append({"name": meta.get("name", p.stem), "file": p.name, "parts": len(meta.get("topology") or []), "example": True})
                            except Exception:
                                pass
                    response = {
                        "status": "success",
                        "action": "list_projects",
                        "projects": items,
                        "examples": examples,
                        "message": f"{len(items)} projects · {len(examples)} examples",
                    }

                elif action == "load_project":
                    fname = data.get("file") or data.get("name") or ""
                    base = Path(str(fname)).name  # strip directories / traversal
                    if base and not base.endswith(".vortexa.json"):
                        base = safe_name(base.replace(".json", ""), "project") + ".vortexa.json"
                    path = None
                    if base:
                        for root in (ROOT / "projects", ROOT / "assets" / "examples"):
                            try:
                                cand = resolve_under(root, base)
                            except PermissionError:
                                continue
                            if cand.is_file():
                                path = cand
                                break
                    if path is None:
                        response = {"status": "error", "action": "load_project", "message": "Project file not found"}
                    else:
                        project = json.loads(path.read_text(encoding="utf-8"))
                        response = {
                            "status": "success",
                            "action": "load_project",
                            "project": project,
                            "file": path.name,
                            "message": f"Loaded {project.get('name', path.name)}",
                        }

                else:
                    response = {
                        "status": "error",
                        "message": f"Unknown action: {action}",
                        "supported": [
                            "load_template", "compute_fk", "compute_ik",
                            "compute_dynamics", "compile_urdf", "export_pybullet",
                            "export_ros2", "export_mjcf", "plan_cartesian",
                            "kit_catalog", "command", "select_chain", "export_trajectory", "list_presets", "apply_preset", "export_usd", "collision_check", "import_urdf", "motion_save", "motion_list", "health", "validate_robot", "enrich_physics", "save_project", "list_projects", "load_project"
                        ]
                    }

                await websocket.send(json.dumps(response))

            except Exception as e:
                logger.exception("Error processing action %s", action)
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": str(e),
                    "action": action,
                }))

    except websockets.exceptions.ConnectionClosed as e:
        logger.info("Client disconnected: %s (code=%s)", client, e.code)
    except Exception as e:
        logger.exception("Unexpected error for client %s: %s", client, e)


async def main():
    host = os.environ.get("VORTEXA_HOST", "127.0.0.1")
    # Force localhost by default — LAN requires VORTEXA_ALLOW_LAN=1
    if host not in ("127.0.0.1", "localhost", "::1") and os.environ.get("VORTEXA_ALLOW_LAN") != "1":
        logger.warning("Host %s overridden to 127.0.0.1 (set VORTEXA_ALLOW_LAN=1 to expose)", host)
        host = "127.0.0.1"
    port = int(os.environ.get("VORTEXA_PORT", "8766"))
    logger.info("Vortexa Studio Bridge v%s starting on ws://%s:%s", APP_VERSION, host, port)
    print(f"VortexaBridge v{APP_VERSION} listening ws://{host}:{port}", flush=True)
    print(f"VORTEXA_TOKEN={SESSION_TOKEN}", flush=True)
    # write token for local UI bootstrap
    try:
        (ROOT / "config" / "session.json").write_text(
            json.dumps({"token": SESSION_TOKEN, "version": APP_VERSION,
                        "token": SESSION_TOKEN, "ws": f"ws://{host}:{port}"}),
            encoding="utf-8",
        )
    except Exception:
        pass
    async with serve(
        handle_client,
        host,
        port,
        ping_interval=30,
        ping_timeout=30,
        max_size=2 * 1024 * 1024,
    ):
        await asyncio.Future()


if __name__ == "__main__":
    # Unbuffered-friendly banner so Termux redirects always show something
    print("Vortexa server.py starting…", flush=True)
    try:
        asyncio.run(main())
    except OSError as e:
        print(f"FAILED to bind socket: {e}", flush=True)
        logger.exception("Bind failed")
        raise
    except KeyboardInterrupt:
        logger.info("Vortexa Bridge shut down cleanly.")
        print("Vortexa Bridge shut down.", flush=True)
