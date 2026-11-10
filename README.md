# Vortexa Studio v3.5

Offline robot design for **phone · PC · web**. Author, validate, and export sim-ready robots.

## What’s new (3.2 → 3.5)

### Sim-ready (3.2)
- **Validate** — graded health report (mass, inertia, limits, tree, DoF)
- **Auto-fill physics** — mass from material density, inertia tensors, joint limits, collision primitives
- Stronger URDF collision + materials (steel / ABS)

### Projects & mesh (3.3)
- **Save Project** → `.vortexa.json` on device
- **Examples** — 6-DoF pick cell, diff rover, dual-arm handoff
- Attach **STL/OBJ** visual mesh to a selected part (stored in project)

### Scene & dual-arm (3.4)
- Scene obstacles (table / box) in the viewport
- Dual-arm helper: IK active chain, then pose the other

### Ready-to-use (3.5)
- First-run welcome (example / blank / skip)
- Desktop: `./launch_desktop.sh` → http://127.0.0.1:8080/?v=35
- Phone: `texup` → same URL

## Workspaces
Object · Edit · Sculpt · Animate · Control

## Export
URDF · ROS 2 package · MuJoCo MJCF · USD (Isaac) · Trajectory CSV

## Quick start
```bash
# Termux
texup
# http://127.0.0.1:8080/?v=35

# Desktop
./launch_desktop.sh
```
