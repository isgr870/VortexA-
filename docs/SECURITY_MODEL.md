# Security model

1. **Network**: default bind `127.0.0.1`. LAN requires explicit env flag.
2. **Auth**: ephemeral `VORTEXA_TOKEN` for mutating/export actions; UI reads it from health response.
3. **Paths**: `scripts/security.safe_name` + `resolve_under` for reads/writes.
4. **Origins**: browser `Origin` checked against allowlist when present.
5. **Input**: max WebSocket message size capped; further schema validation is ongoing.
