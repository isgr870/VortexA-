"""Security helper and path containment tests."""
from pathlib import Path
import pytest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.security import safe_name, safe_template_name, resolve_under


def test_safe_name_strips_traversal():
    assert ".." not in safe_name("../etc/passwd")
    assert "/" not in safe_name("a/b")
    assert safe_name(None) == "vortexa"


def test_safe_template_rejects_junk():
    assert safe_template_name("articulated_arm") == "articulated_arm"
    assert safe_template_name("../../x") == "articulated_arm"
    assert safe_template_name(None) == "articulated_arm"


def test_resolve_under_blocks_escape(tmp_path):
    root = tmp_path / "urdf"
    root.mkdir()
    ok = resolve_under(root, "robot.urdf")
    assert ok.parent == root.resolve()
    with pytest.raises(PermissionError):
        resolve_under(root, "..", "outside.txt")


def test_version_file():
    v = (ROOT / "VERSION").read_text().strip()
    assert v.count(".") >= 1
    assert v.startswith("3.")
