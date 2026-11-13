#!/usr/bin/env bash
# Remove tracked junk that must not ship in a production repo
set -euo pipefail
cd "$(dirname "$0")/.."
git rm -r --cached '~' 2>/dev/null || true
git rm --cached VortexA-1.zip 2>/dev/null || true
git rm --cached urdf/*.urdf urdf/*.xml urdf/*.usda 2>/dev/null || true
git rm -r --cached urdf/motions 2>/dev/null || true
git update-index --chmod=+x texup texoff launch_desktop.sh launch_vortexa.sh 2>/dev/null || true
echo "Hygiene staging done — review git status and commit"
