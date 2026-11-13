# Architecture

```
Browser (index.html + Three.js)
    |  HTTP :8080  (static UI)
    |  WebSocket :8766
server.py  (local bridge)
    |-- scripts/kinematics_engine.py
    |-- scripts/health_validator.py
    |-- scripts/*_export.py
    +-- assets/templates, kit, examples
```

## Trust boundary
The WebSocket bridge is a **local computation service**. Treat it like a developer tool bound to localhost. Do not expose it to the public internet without authentication, TLS, and a hardened deployment review.

## Capabilities vs claims
| Feature | Status |
|---------|--------|
| Serial-chain FK / position IK | Implemented |
| Multi-chain templates | Partial (active chain) |
| Collision check | Heuristic — not pose-complete safety |
| Health score | Structural heuristic — not simulator certification |
| Physical motor control | Not implemented |
