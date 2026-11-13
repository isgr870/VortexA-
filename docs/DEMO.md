# Demo strategy

## Full product loop (recommended for investors)
Shows Connected UI + FK/IK + export.

| Audience | Path |
|----------|------|
| Phone | Termux: `texup` → browser `http://127.0.0.1:8080` |
| Laptop | [Release](https://github.com/isgr870/VortexA-/releases) desktop zip, or `python packaging/desktop_entry.py` |

**60-second script**
1. Launch → status **Connected** / version 3.6.x  
2. TexaKit → **6-DoF Industrial Arm**  
3. Drag joints · Control → Home  
4. **Validate** · **Export URDF**  
5. Open the URDF path shown in the status panel  

## GitHub Pages (optional UI preview)
Static hosting can show the shell and 3D viewport **only if** a bridge is available.  
Without `server.py` on the machine, the UI stays Offline for compute actions.

Do **not** market Pages as a full cloud robotics CAD until a hosted bridge exists.

## What not to claim in a pitch
- Physical robot motion  
- Certified collision safety  
- Drop-in Isaac/Gazebo acceptance without tuning  
