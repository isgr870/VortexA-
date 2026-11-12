# Contributing to Vortexa Studio

## Principles
1. **Offline-first** — no hard dependency on cloud APIs for core design/export
2. **Termux-safe** — avoid features that break on Android/Python limited environments
3. **Sim-ready** — exports should prefer valid mass/inertia/limits/collision
4. **Small diffs** — one focused change per PR when possible

## Setup
```bash
pip install -r requirements.txt
python3 -u server.py   # port 8766
python3 -m http.server 8080 --bind 127.0.0.1
```

## Useful areas
- `scripts/kinematics_engine.py` — FK/IK
- `scripts/health_validator.py` — sim-ready scoring
- `scripts/*_export.py` / `urdf_generator_api.py` — exporters
- `assets/templates/` — new blueprints (JSON)
- `index.html` — UI/workspaces (keep mobile usable)

## Pull requests
- Describe user-visible behavior
- Note Termux tested yes/no
- Update CHANGELOG.md under a new version section if behavior changes
