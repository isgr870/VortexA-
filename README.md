# Vortexa Studio

**Offline-first robot design studio** for phone, PC, and web.
Author manipulators, mobile robots, humanoids, and drones — validate for simulation — export to **URDF · ROS 2 · MuJoCo · USD (Isaac)**.

Version **3.5.4** · Python 3.10+ · MIT License

## Features

- **TexaKit** — blueprints + parts library (structure, joints, wheels, sensors, power, end effectors)
- **Workspaces** — Object · Edit · Sculpt · Animate · Control
- **Kinematics** — FK / damped IK, reach, TCP, multi-chain (dual-arm, hexapod)
- **Sim-ready health** — mass, inertia, limits, tree checks (graded report)
- **Projects** — save/load `.vortexa.json`, bundled examples
- **Exports** — URDF, ROS 2 package, MuJoCo MJCF, OpenUSD, trajectory CSV
- **Offline** — vendored Three.js; runs on Termux without cloud

## Quick start

```bash
git clone https://github.com/<you>/VortexA.git
cd VortexA
pip install -r requirements.txt

# Desktop
chmod +x launch_desktop.sh && ./launch_desktop.sh

# Or Termux
chmod +x texup texoff && ./texup
```

Open **http://127.0.0.1:8080/?v=354** → green **Connected** → pick a blueprint.

More detail: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)

## Architecture

```
Browser (index.html + Three.js)  --HTTP :8080-->  python -m http.server
         |
         +-- WebSocket :8766 --> server.py --> scripts/
             (kinematics, URDF, MJCF, USD, health)
```

All compute stays local. No account, no GPU required for authoring.

## Repository layout

```
VortexA/
├── server.py              # WebSocket bridge
├── index.html             # Studio UI
├── requirements.txt
├── texup / texoff         # Termux helpers
├── launch_desktop.sh      # Desktop / LAN
├── scripts/               # Engines & exporters
├── assets/
│   ├── templates/         # Robot blueprints
│   ├── kit/               # Parts, presets, catalog
│   └── examples/          # Sample projects
├── vendor/three/          # Offline Three.js
├── docs/
└── tests/
```

## Exports

| Format | Use |
|--------|-----|
| URDF | Gazebo, RViz, generic ROS |
| ROS 2 package | package.xml + tree |
| MJCF | MuJoCo |
| USD/USDA | NVIDIA Isaac Sim |
| Trajectory CSV | Joint timeseries |

## Development

```bash
python3 -u server.py          # VORTEXA_PORT=8766
python3 -m http.server 8080 --bind 127.0.0.1
```

See [CHANGELOG.md](CHANGELOG.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
Three.js is included under its MIT license (Three.js authors).
