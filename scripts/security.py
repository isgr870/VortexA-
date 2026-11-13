"""Path and name safety for Vortexa bridge."""
from __future__ import annotations
import re
from pathlib import Path

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SAFE_TEMPLATE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

def safe_name(name: str | None, default: str = "vortexa") -> str:
    if not name or not isinstance(name, str):
        return default
    name = name.strip().replace(" ", "_")
    if not SAFE_NAME_RE.match(name):
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:64].strip("._-")
        return cleaned or default
    return name

def safe_template_name(name: str | None, default: str = "articulated_arm") -> str:
    if not name or not isinstance(name, str):
        return default
    name = name.strip()
    if not SAFE_TEMPLATE_RE.match(name):
        return default
    return name

def resolve_under(root: Path, *parts: str) -> Path:
    """Resolve path and require it stays under root (no traversal)."""
    root = root.resolve()
    candidate = root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise PermissionError(f"Path escapes allowed directory: {candidate}") from e
    return candidate
