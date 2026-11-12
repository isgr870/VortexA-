# Getting started — Vortexa Studio

## Requirements
- Python 3.10+
- `pip install -r requirements.txt` (`numpy`, `websockets`)
- Modern browser (Chrome, Firefox, Edge)

## Phone (Termux / Android)
```bash
cd ~/VortexA   # or your clone path
pip install -r requirements.txt
chmod +x texup texoff
./texup
# Open http://127.0.0.1:8080/?v=354
```

If the pill stays **Offline**:
```bash
export VORTEXA_PORT=8766 VORTEXA_HOST=127.0.0.1
python3 -u server.py          # terminal A
python3 -m http.server 8080 --bind 127.0.0.1   # terminal B
```

## Desktop
```bash
cd VortexA
pip install -r requirements.txt
chmod +x launch_desktop.sh
./launch_desktop.sh
# http://127.0.0.1:8080/?v=354
```

## First actions
1. Wait for green **Connected**
2. TexaKit → **6-DoF Industrial Arm** (or **Examples** on Status)
3. **Validate** → health grade on Status
4. **Export URDF** / ROS 2 / MuJoCo / USD

## Layout
| Path | Role |
|------|------|
| `server.py` | WebSocket bridge (default `ws://127.0.0.1:8766`) |
| `index.html` | Studio UI |
| `scripts/` | Kinematics, exports, health validator |
| `assets/templates/` | Blueprint JSON |
| `assets/kit/` | TexaKit catalog, parts, presets |
| `assets/examples/` | Sample `.vortexa.json` projects |
| `vendor/three/` | Offline Three.js |

## Ports
- UI: `8080`
- Bridge: `8766` (`VORTEXA_PORT`)
