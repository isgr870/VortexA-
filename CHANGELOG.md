# Changelog

## 3.6.4 — 2026-11-21
- **Fix:** Desktop PyInstaller bundles omit `xml.etree` → bridge crash on startup
  - Explicit hidden-imports + collect-submodules for `xml*`
  - Force-import in `packaging/desktop_entry.py` so analysis cannot drop them
  - Hidden-imports for `scripts.*` exporters used by the bridge
- Rebuild Windows / Linux / macOS desktop artifacts required after this tag

## 3.6.3 — 2026-11-13
- Investor package: INVESTOR brief, EXPORTS matrix, DEMO strategy
- README positioned for discovery and diligence

## 3.6.2 — 2026-11-13
- ROADMAP, PRODUCT, Code of Conduct; experimental collision labeling

## 3.6.1 — 2026-11-13
- pytest CI, hygiene, SECURITY, professional baseline

## 3.6.0 — 2026-11-13
- P0 security + desktop packaging
