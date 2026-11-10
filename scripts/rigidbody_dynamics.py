"""
Vortexa Studio - Rigid Body Dynamics
Computes approximate mass matrices and link inertias for serial chains.
"""

from __future__ import annotations

import numpy as np
from typing import Sequence, Dict, Any, List


class RigidBodyDynamics:
    """
    Lightweight rigid-body dynamics helpers for design-time analysis.
    Not a full recursive Newton-Euler implementation; intended for
    rapid mass-property estimation and export validation.
    """

    def __init__(self, robot_topology: Sequence[Dict[str, Any]]):
        self.topology = list(robot_topology)

    def compute_mass_matrix(self, joint_angles: Sequence[float] | None = None) -> List[List[float]]:
        """
        Return a simple diagonal approximation of the joint-space mass matrix.
        For design purposes only. Full articulated-body inertia requires
        recursive algorithms (ABA / CRBA) which can be added later.
        """
        n = sum(1 for link in self.topology if link.get("type") != "fixed")
        M = np.zeros((n, n))

        joint_idx = 0
        for link in self.topology:
            if link.get("type") == "fixed":
                continue
            mass = float(link.get("mass", 1.0))
            length = float(link.get("length", 0.3))
            # Simple rod-about-end inertia contribution projected to joint
            # I = (1/3) m L² for a thin rod
            M[joint_idx, joint_idx] = mass * (length ** 2) / 3.0
            joint_idx += 1

        return M.tolist()

    def link_inertias(self) -> List[Dict[str, float]]:
        """
        Approximate principal inertias for each link (cylinder assumption).
        Useful for populating correct <inertial> blocks in URDF.
        """
        results = []
        for link in self.topology:
            mass = float(link.get("mass", 1.0))
            length = float(link.get("length", 0.3))
            radius = float(link.get("radius", 0.05))

            # Solid cylinder inertia about center of mass
            # Izz (along axis) = 0.5 m r²
            # Ixx = Iyy = (1/12) m (3r² + h²)
            izz = 0.5 * mass * radius ** 2
            ixx = iyy = (1.0 / 12.0) * mass * (3 * radius ** 2 + length ** 2)

            results.append({
                "name": link.get("name", "link"),
                "mass": mass,
                "ixx": ixx,
                "iyy": iyy,
                "izz": izz,
                "ixy": 0.0,
                "ixz": 0.0,
                "iyz": 0.0,
            })
        return results
