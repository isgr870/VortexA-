# Vortexa Studio

[![CI](https://github.com/isgr870/VortexA-/actions/workflows/ci.yml/badge.svg)](https://github.com/isgr870/VortexA-/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.6.2-informational)](VERSION)

**Offline-first robot design studio** for phone, desktop, and web.  
Author manipulators and mobile robots → validate structure → export **URDF · ROS 2 · MuJoCo · USD**.

> Honest scope: serial-chain design and export toolkit — **not** a certified physics simulator or motor controller.

## Downloads

| Platform | How |
|----------|-----|
| **Windows / Linux / macOS** | [Actions → Build Desktop](https://github.com/isgr870/VortexA-/actions) artifacts, or [Releases](https://github.com/isgr870/VortexA-/releases) |
| **Termux** | `./texup` → http://127.0.0.1:8080 |
| **Web / PWA** | Build Web workflow |

Extract the desktop zip and run the app — no manual Python setup required for those bundles.

## Quick start (from source)

```bash
git clone https://github.com/isgr870/VortexA-.git
cd VortexA-
python -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements-dev.txt
pytest -q
python scripts/demo_smoke.py
python packaging/desktop_entry.py
```

## Demo path (60s)
1. Start → Connected  
2. TexaKit → **6-DoF Industrial Arm**  
3. Joints → pose · **Validate** · **Export URDF**

## Repository layout

```
server.py              WebSocket bridge (localhost by default)
index.html             Studio UI
scripts/               Kinematics, export, security, smoke
assets/templates/      Robot blueprints
assets/examples/       Sample projects
tests/                 pytest suite
packaging/             Desktop entry + mobile notes
.github/workflows/     CI, desktop, web, release
docs/                  Architecture & security model
```

## Security defaults
- Bind **127.0.0.1** only (`VORTEXA_ALLOW_LAN=1` to expose)
- Session token required for export / project file ops  
- Path containment for reads/writes  

See [SECURITY.md](SECURITY.md) and [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md).

## Roadmap
See [ROADMAP.md](ROADMAP.md) and [docs/PRODUCT.md](docs/PRODUCT.md).

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). Open issues with the templates under `.github/ISSUE_TEMPLATE/`.

## License
MIT — [LICENSE](LICENSE)
