# Vortexa Studio — Investor brief

## Problem
Robot teams and students need a fast way to **author and export** robot structures before entering heavy toolchains (ROS, MuJoCo, Isaac). Those toolchains assume a model already exists. Phones and offline labs are poorly served.

## Solution
**Vortexa Studio** — offline-first design studio:
- Visual robot authoring (blueprints + joints + 3D view)
- Structural validation
- Export to **URDF · ROS 2 · MuJoCo · USD**
- Runs on **Termux (phone)**, desktop bundles, and local web

## Product stage
Early **design & export** studio (v3.6.x).  
Not a physics certification suite or motor controller.

## Traction evidence (engineering)
- Public MIT repo with CI (pytest + smoke)
- Security defaults: localhost bind, session token, path containment
- Branch protection on `main`
- Desktop packaging workflows (Windows / Linux / macOS)
- Documented roadmap and explicit non-goals

## Market wedge
Education · research labs · early robotics startups · freelance automation integrators who need a clean authoring step before simulation.

## Ask
Capital or partnership to fund:
1. Deeper kinematics (branched trees, 6D IK)
2. Exporter validation against real simulators
3. Production mobile packaging (APK with clear bridge story)

## Links
- Repo: https://github.com/isgr870/VortexA-
- Product: [PRODUCT.md](PRODUCT.md)
- Roadmap: [../ROADMAP.md](../ROADMAP.md)
- Security: [../SECURITY.md](../SECURITY.md)
