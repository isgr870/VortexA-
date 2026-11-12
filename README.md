# Vortexa Studio

**Offline-first robot design studio** for phone, PC, and web.  
Author manipulators, mobile robots, humanoids, and drones — validate for simulation — export **URDF · ROS 2 · MuJoCo · USD**.

Version **3.5.11** · Python 3.10+ · MIT License

## Demo path (60 seconds)
1. Start bridge: `./texup` (Termux) or `./launch_desktop.sh`
2. Open http://127.0.0.1:8080/?v=3510 → **Connected**
3. TexaKit → **6-DoF Industrial Arm**
4. **Joints** — drag live pose · **Control** — Home / jog
5. **Validate** → **Export URDF**

Automated smoke: `python scripts/demo_smoke.py`

## Quick start
```bash
git clone https://github.com/isgr870/VortexA-.git
cd VortexA-
pip install -r requirements.txt
python scripts/demo_smoke.py
./launch_desktop.sh   # or ./texup on Termux
```

## Packaging
| Target | How |
|--------|-----|
| Web / PWA | Static UI + local bridge · workflow `Build Web` |
| Windows / Linux | PyInstaller · workflow `Build Desktop` |
| Android / iOS | Capacitor shell · see `packaging/MOBILE.md` |

Run workflows from the GitHub **Actions** tab (`workflow_dispatch` or version tags `v*`).

## Architecture
```
Browser UI (Three.js) --HTTP :8080--> static files
       |
       +-- WebSocket :8766 --> server.py --> scripts/ (FK, IK, export, health)
```

## Repository
- `server.py` — local computation bridge  
- `index.html` — Studio UI (VortexaCore + VortexaView)  
- `assets/templates` — blueprints  
- `scripts/demo_smoke.py` — CI / investor regression  

## License
MIT — see [LICENSE](LICENSE).
