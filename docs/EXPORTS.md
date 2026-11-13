# Export formats

Vortexa authors a robot topology, then emits files other tools can load.  
Exports are **design-time deliverables**. Always validate in the target simulator before hardware use.

| Format | File / output | Best for | Limitations |
|--------|----------------|----------|-------------|
| **URDF** | `urdf/<name>.urdf` | ROS, Gazebo, MoveIt, many importers | Serial-chain oriented; mesh geometry is primitive capsules/boxes |
| **ROS 2** | Package skeleton (`*_description`) | Starting a ROS 2 workspace | Skeleton only — not a full tested colcon package |
| **MuJoCo (MJCF)** | `urdf/<name>.xml` | MuJoCo research sims | Serial body chain; tune contacts/actuators in MuJoCo |
| **USD / USDA** | `urdf/<name>.usda` | Omniverse / Isaac **geometry handoff** | Joint metadata is limited — not a full physics robot definition |
| **Trajectory CSV** | `urdf/<name>_trajectory.csv` | Plotting, ROS bag pipelines, analysis | Joint timeseries only |
| **PyBullet script** | Generated Python text | Quick script bootstrap | Simulator not bundled or executed by Vortexa |

## Recommended path
1. Design + joint pose in Studio  
2. **Validate** (structural health — heuristic)  
3. Export **URDF** as the interchange baseline  
4. Load in Gazebo / MuJoCo / Isaac and fix unit, inertia, and collision details there  

## What “sim-ready” means here
Structural completeness for export (links, joints, masses, limits) — **not** a certificate that a given simulator loaded the model without edits.
