"""
Vortexa Studio - Kinematics Engine v2.2
Industry-oriented Forward / Inverse Kinematics (NumPy).
- Explicit axis handling
- Joint limit awareness
- Damped least-squares Jacobian IK
- Manipulability metric (Yoshikawa)
"""

from __future__ import annotations

import numpy as np
from typing import List, Optional, Sequence, Dict, Any, Tuple


def _rotation_matrix(axis: str, angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    R = np.eye(4)
    axis = (axis or "z").lower()
    if axis == "x":
        R[1, 1] = c; R[1, 2] = -s; R[2, 1] = s; R[2, 2] = c
    elif axis == "y":
        R[0, 0] = c; R[0, 2] = s; R[2, 0] = -s; R[2, 2] = c
    else:
        R[0, 0] = c; R[0, 1] = -s; R[1, 0] = s; R[1, 1] = c
    return R


def _translation_matrix(length: float, axis: str = "z") -> np.ndarray:
    T = np.eye(4)
    axis = (axis or "z").lower()
    if axis == "x":
        T[0, 3] = length
    elif axis == "y":
        T[1, 3] = length
    else:
        T[2, 3] = length
    return T


class KinematicsEngine:
    """Serial-chain FK / IK with joint limits and basic manipulability."""

    def __init__(self, robot_topology: Sequence[Dict[str, Any]]):
        self.topology = list(robot_topology)
        self.active = [link for link in self.topology if link.get("type") != "fixed"]
        self.n_joints = len(self.active)
        self.limits = self._extract_limits()

    def _extract_limits(self) -> List[Tuple[float, float]]:
        limits = []
        for link in self.active:
            lim = link.get("limit") or {}
            lo = float(lim.get("lower", -np.pi))
            hi = float(lim.get("upper", np.pi))
            if lo > hi:
                lo, hi = hi, lo
            limits.append((lo, hi))
        return limits

    def clamp_angles(self, angles: Sequence[float]) -> np.ndarray:
        a = np.array(angles, dtype=float)
        if len(a) < self.n_joints:
            a = np.pad(a, (0, self.n_joints - len(a)))
        a = a[: self.n_joints]
        for i, (lo, hi) in enumerate(self.limits):
            a[i] = float(np.clip(a[i], lo, hi))
        return a

    def forward_kinematics(self, joint_angles: Sequence[float]) -> np.ndarray:
        angles = list(joint_angles)
        transform = np.eye(4)
        angle_idx = 0

        for link in self.topology:
            link_type = link.get("type", "revolute")
            axis = link.get("axis", "z")
            length = float(link.get("length", 0.3))

            if link_type == "fixed":
                transform = transform @ _translation_matrix(length, "z")
                continue

            angle = float(angles[angle_idx]) if angle_idx < len(angles) else 0.0
            angle_idx += 1

            if link_type in ("revolute", "continuous"):
                transform = transform @ _rotation_matrix(axis, angle) @ _translation_matrix(length, "z")
            elif link_type == "prismatic":
                transform = transform @ _translation_matrix(length + angle, axis)
            else:
                transform = transform @ _translation_matrix(length, "z")

        return transform

    def end_effector_position(self, joint_angles: Sequence[float]) -> np.ndarray:
        return self.forward_kinematics(joint_angles)[:3, 3].copy()

    def jacobian_position(self, joint_angles: Sequence[float], eps: float = 1e-6) -> np.ndarray:
        """Numerical 3 x n positional Jacobian (respects TCP offset when set)."""
        n = self.n_joints
        angles = np.array(joint_angles, dtype=float)
        if len(angles) < n:
            angles = np.pad(angles, (0, n - len(angles)))
        use_tcp = any(abs(v) > 1e-9 for v in getattr(self, "tcp_xyz", [0, 0, 0]))
        ee = self.end_effector_position_tcp if use_tcp else self.end_effector_position
        base = ee(angles)
        J = np.zeros((3, n))
        for i in range(n):
            a2 = angles.copy()
            a2[i] += eps
            J[:, i] = (ee(a2) - base) / eps
        return J

    def manipulability(self, joint_angles: Sequence[float]) -> float:
        """Yoshikawa manipulability: sqrt(det(J J^T)) with SVD fallback."""
        J = self.jacobian_position(joint_angles)
        try:
            # Prefer product of singular values (numerically stable)
            s = np.linalg.svd(J, compute_uv=False)
            s = np.clip(s, 0.0, None)
            return float(np.prod(s))
        except Exception:
            try:
                return float(np.sqrt(max(0.0, np.linalg.det(J @ J.T))))
            except Exception:
                return 0.0

    def singularity_index(self, joint_angles: Sequence[float]) -> dict:
        """Return manipulability, min singular value, and near_singularity flag."""
        J = self.jacobian_position(joint_angles)
        try:
            s = np.linalg.svd(J, compute_uv=False)
            s = np.clip(s, 0.0, None)
            mu = float(np.prod(s))
            smin = float(s.min()) if len(s) else 0.0
        except Exception:
            mu, smin = 0.0, 0.0
        return {
            "manipulability": mu,
            "sigma_min": smin,
            "near_singularity": bool(smin < 1e-3),
        }

    def max_reach(self) -> float:
        """Upper bound on reach: sum of link lengths."""
        return float(sum(float(l.get("length", 0.0)) for l in self.topology))

    def clamp_target_to_workspace(self, target: Sequence[float], margin: float = 0.02) -> np.ndarray:
        t = np.array(target, dtype=float)
        rmax = max(0.05, self.max_reach() - margin)
        n = np.linalg.norm(t)
        if n > rmax and n > 1e-9:
            t = t * (rmax / n)
        # Keep above ground-ish in robot Z
        t[2] = max(0.05, t[2])
        return t

    def solve_ik(
        self,
        target_position: Sequence[float],
        initial_angles: Optional[Sequence[float]] = None,
        max_iters: int = 120,
        tol: float = 1e-4,
        damping: float = 0.08,
        step_size: float = 0.6,
        respect_limits: bool = True,
    ) -> Dict[str, Any]:
        """
        Damped least-squares IK.
        Returns dict with joint_angles, residual, success, manipulability, iterations.
        """
        n = self.n_joints
        if n == 0:
            return {
                "joint_angles": [],
                "residual": 0.0,
                "success": True,
                "manipulability": 0.0,
                "iterations": 0,
            }

        if initial_angles is None:
            angles = np.zeros(n)
        else:
            angles = np.array(initial_angles, dtype=float)
            if len(angles) < n:
                angles = np.pad(angles, (0, n - len(angles)))
            angles = angles[:n]

        if respect_limits:
            angles = self.clamp_angles(angles)

        target = self.clamp_target_to_workspace(target_position)
        use_tcp = any(abs(v) > 1e-9 for v in getattr(self, "tcp_xyz", [0, 0, 0]))
        residual = 0.0
        it = 0

        for it in range(max_iters):
            pos = self.end_effector_position_tcp(angles) if use_tcp else self.end_effector_position(angles)
            error = target - pos
            residual = float(np.linalg.norm(error))
            if residual < tol:
                break

            J = self.jacobian_position(angles)
            # Damped least squares: dq = J^T (J J^T + λ² I)^{-1} e
            JJT = J @ J.T
            lam2 = (damping ** 2) * np.eye(3)
            try:
                dq = J.T @ np.linalg.solve(JJT + lam2, error)
            except np.linalg.LinAlgError:
                dq = J.T @ (np.linalg.pinv(JJT + lam2) @ error)

            angles = angles + step_size * dq
            if respect_limits:
                angles = self.clamp_angles(angles)

        success = residual < max(tol * 10, 0.005)  # practical success band (~5mm)
        sing = self.singularity_index(angles)
        return {
            "joint_angles": [float(a) for a in angles],
            "residual": residual,
            "success": bool(success),
            "manipulability": sing["manipulability"],
            "sigma_min": sing["sigma_min"],
            "near_singularity": sing["near_singularity"],
            "iterations": it + 1,
            "end_effector_position": (self.end_effector_position_tcp(angles) if use_tcp else self.end_effector_position(angles)).tolist(),
            "target_used": target.tolist(),
            "max_reach": self.max_reach(),
        }


    def set_tcp_offset(self, xyz=None, rpy=None):
        """Tool frame offset relative to last link flange (meters, radians)."""
        self.tcp_xyz = list(xyz or [0.0, 0.0, 0.0])
        self.tcp_rpy = list(rpy or [0.0, 0.0, 0.0])

    def _tcp_matrix(self):
        x, y, z = getattr(self, "tcp_xyz", [0, 0, 0])
        rr, pp, yy = getattr(self, "tcp_rpy", [0, 0, 0])
        cx, sx = np.cos(rr), np.sin(rr)
        cy, sy = np.cos(pp), np.sin(pp)
        cz, sz = np.cos(yy), np.sin(yy)
        # ZYX
        R = np.array([
            [cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
            [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
            [-sy,   cy*sx,            cy*cx],
        ], dtype=float)
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [x, y, z]
        return T

    def forward_kinematics_tcp(self, joint_angles):
        """FK including tool frame offset."""
        return self.forward_kinematics(joint_angles) @ self._tcp_matrix()

    def end_effector_position_tcp(self, joint_angles):
        return self.forward_kinematics_tcp(joint_angles)[:3, 3].copy()

