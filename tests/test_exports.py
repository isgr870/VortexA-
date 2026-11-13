"""Exporter smoke tests."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.urdf_generator_api import generate_urdf
from scripts.mjcf_export import generate_mjcf


def links():
    return json.loads((ROOT / "assets" / "templates" / "articulated_arm.json").read_text())["links"]


def test_urdf_has_robot_and_links():
    try:
        urdf = generate_urdf(links(), robot_name="unit_test_arm")
    except TypeError:
        urdf = generate_urdf(links(), "unit_test_arm")
    if isinstance(urdf, tuple):
        urdf = urdf[0]
    assert isinstance(urdf, str)
    assert "<robot" in urdf
    assert "link" in urdf.lower()


def test_mjcf_nonempty():
    try:
        mj = generate_mjcf(links(), robot_name="unit_test_arm")
    except TypeError:
        mj = generate_mjcf(links(), "unit_test_arm")
    assert isinstance(mj, str) and len(mj) > 50
