# Packaging

- `desktop_entry.py` — opens browser + starts `server.py` / static HTTP (PyInstaller entry)
- `MOBILE.md` — Capacitor APK / iOS plan
- GitHub Actions:
  - `.github/workflows/ci.yml` — smoke tests
  - `.github/workflows/build-desktop.yml` — Linux + Windows artifacts
  - `.github/workflows/build-web.yml` — static PWA folder
