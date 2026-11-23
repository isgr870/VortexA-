# Security Policy

## Supported versions
| Version | Supported |
|---------|-----------|
| 3.6.x   | Yes |
| < 3.6   | Limited |

## Default posture
- Bridge binds to **127.0.0.1** only unless `VORTEXA_ALLOW_LAN=1`.
- Export and project filesystem actions require a **session token** issued at bridge start.
- Project load and export paths are constrained under `projects/`, `assets/examples/`, and `urdf/`.

## Reporting a vulnerability
Open a private security advisory on GitHub, or email the maintainer listed on the repository profile.
Please include version, environment, and a minimal reproduction.

Do **not** use Vortexa to control physical hardware without an independent safety layer.

## Session token
- Generated at process start; written to `config/session.json` for local clients.
- **Not** returned by the `health` action (as of v3.6.5).
- Required for export / project file operations when set.
- Prefer localhost-only bind; set `VORTEXA_ALLOW_LAN=1` only when intentional.
