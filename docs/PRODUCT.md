# Vortexa Studio — Product brief

## One line
Offline robot **design and export** studio: sketch kinematics, validate structure, ship URDF / ROS 2 / MuJoCo / USD.

## Who it is for
- Students and labs teaching robot modeling without heavy installs
- Engineers prototyping arm / mobile topologies on phone or laptop
- Teams that need a clean authoring step **before** full simulators

## What works today
| Capability | Status |
|------------|--------|
| Blueprint library (arms, humanoid, hexapod, rover, quadrotor) | Yes |
| 3D view + joint control + position IK | Yes |
| Structural health scoring | Heuristic |
| URDF / ROS 2 package skeleton / MJCF / USD export | Yes |
| Local offline operation (Termux + desktop) | Yes |
| Physical robot control | No |
| Certified collision safety | No |

## Differentiation
- **Offline-first** and phone-capable (Termux), not cloud-locked
- End-to-end path: template → pose → validate → export
- Honest labeling of experimental vs production-grade features

## Business readiness
- MIT licensed public core
- CI, security policy, branch protection on `main`
- Installer workflows for Windows / Linux / macOS

## Ask for partners / investors
Funding or collaboration should target: deeper kinematics, exporter certification pipelines, and mobile packaging — not a rewrite of the existing design loop.
