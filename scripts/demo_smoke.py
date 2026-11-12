#!/usr/bin/env python3
"""Investor/CI smoke path: templates → FK → validate → URDF."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kinematics_engine import KinematicsEngine
from scripts.health_validator import validate_robot
from scripts.urdf_generator_api import generate_urdf


def load_links(name: str) -> list:
    data = json.loads((ROOT / "assets" / "templates" / f"{name}.json").read_text(encoding="utf-8"))
    if data.get("multi_chain") and data.get("chains"):
        chains = data["chains"]
        body = "torso" if "torso" in chains else ("body" if "body" in chains else None)
        active = data.get("default_chain") or next(iter(chains))
        topo = list(chains[body]) if body and active != body else []
        return topo + list(chains[active])
    return list(data.get("links") or data.get("topology") or [])


def main() -> int:
    templates = sorted(p.stem for p in (ROOT / "assets" / "templates").glob("*.json"))
    assert templates, "no templates"
    failed = []
    for name in templates:
        links = load_links(name)
        if not links:
            failed.append(f"{name}: empty links")
            continue
        try:
            eng = KinematicsEngine(links)
            q = [0.0] * eng.n_joints
            if eng.n_joints >= 3:
                q[1] = -0.5
                q[2] = 0.8
            eng.forward_kinematics(q)
            report = validate_robot(links, robot_name=name)
            urdf = generate_urdf(links, robot_name=name)
            if not isinstance(urdf, str) or "<robot" not in urdf:
                # some APIs return tuple
                if isinstance(urdf, tuple):
                    urdf = urdf[0]
            if not isinstance(urdf, str) or "link" not in urdf.lower():
                failed.append(f"{name}: bad URDF")
                continue
            grade = report.get("grade") if isinstance(report, dict) else "?"
            print(f"OK  {name:24s} parts={len(links):2d} dof={eng.n_joints:2d} grade={grade}")
        except Exception as e:
            failed.append(f"{name}: {e}")
            print(f"FAIL {name}: {e}")

    # Canonical demo path
    links = load_links("articulated_arm")
    eng = KinematicsEngine(links)
    q = [0.0] * eng.n_joints
    if eng.n_joints >= 6:
        q[1], q[2] = -0.6, 1.0
    eng.forward_kinematics(q)
    eng.solve_ik([0.35, 0.0, 0.45], q)
    generate_urdf(links, robot_name="demo_arm")
    print("DEMO_PATH_OK articulated_arm → FK → IK → URDF")

    if failed:
        print("FAILURES:", *failed, sep="\n  ")
        return 1
    print(f"ALL_OK templates={len(templates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
