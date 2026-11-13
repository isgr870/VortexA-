# Vortexa Studio

[![CI](https://github.com/isgr870/VortexA-/actions/workflows/ci.yml/badge.svg)](https://github.com/isgr870/VortexA-/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.6.3-informational)](VERSION)
[![Release](https://img.shields.io/github/v/release/isgr870/VortexA-?sort=semver)](https://github.com/isgr870/VortexA-/releases)

**Offline-first workspace for designing, validating, and exporting robots — on phone, desktop, and web.**

Author manipulators, mobile bases, and research platforms → check structure → export **URDF · ROS 2 · MuJoCo · USD**.

> Honest scope: a **design & export studio**, not a certified physics simulator or hardware controller.

---

## Why Vortexa
| Need | Vortexa |
|------|---------|
| Work offline / on a phone lab | Termux + local bridge |
| Skip heavy installs to start modeling | Templates + 3D joints in minutes |
| Hand off to real toolchains | URDF / ROS 2 / MJCF / USD exports |
| Trust the repo | CI, security policy, protected `main` |

## Downloads
| Platform | Get it |
|----------|--------|
| **Windows / Linux / macOS** | [Latest Release](https://github.com/isgr870/VortexA-/releases) (desktop zips from Actions) |
| **Android (Termux)** | Clone or unzip → `./texup` |
| **Web UI** | Local HTTP + bridge (see [docs/DEMO.md](docs/DEMO.md)) |

Extract a desktop zip and run the app — no manual Python setup for those bundles.

## 60-second demo
1. Start Studio → **Connected**  
2. TexaKit → **6-DoF Industrial Arm**  
3. Joints / Control → pose the arm  
4. **Validate** → **Export URDF**  

Full paths: [docs/DEMO.md](docs/DEMO.md)

## Export formats
| Format | Use |
|--------|-----|
| URDF | ROS, Gazebo, many importers |
| ROS 2 | Description package skeleton |
| MuJoCo MJCF | Research simulation |
| USD/USDA | Omniverse / Isaac geometry handoff |
| Trajectory CSV | Analysis / bag-friendly timeseries |

Details and limits: [docs/EXPORTS.md](docs/EXPORTS.md)

## Quick start (from source)
```bash
git clone https://github.com/isgr870/VortexA-.git
cd VortexA-
pip install -r requirements-dev.txt
pytest -q
python packaging/desktop_entry.py
# or: ./texup   # Termux
```

## Security defaults
- Bind **127.0.0.1** only (`VORTEXA_ALLOW_LAN=1` to expose)
- Session token for export / project file operations  
- Path containment for reads/writes  

[SECURITY.md](SECURITY.md) · [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)

## For investors & partners
- [docs/INVESTOR.md](docs/INVESTOR.md) — brief  
- [docs/PRODUCT.md](docs/PRODUCT.md) — product truth table  
- [ROADMAP.md](ROADMAP.md) — now / next / non-goals  

## Repository layout
```
server.py          Local WebSocket bridge
index.html         Studio UI
scripts/           Kinematics, export, security
assets/templates/  Robot blueprints
tests/             pytest
packaging/         Desktop entry + mobile notes
docs/              Architecture, exports, demo, investor
```

## Contributing
[CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License
MIT — [LICENSE](LICENSE)
