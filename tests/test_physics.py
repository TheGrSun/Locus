import importlib.util
import json
from pathlib import Path

from desmos_mcp.physics import motion, oscillator, projectile


def _demo():
    spec = importlib.util.spec_from_file_location("demo_server", Path(__file__).parents[1] / "demo" / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projectile_lands_at_the_textbook_range():
    result = projectile(10, 45, gravity=10)
    assert result["range"] == 10
    assert abs(result["max_height"] - 2.5) < 1e-6
    assert result["y"][-1] == 0
    assert result["x"][0] == 0 and result["y"][0] == 0


def test_oscillator_returns_to_the_amplitude():
    result = oscillator(2, 1, cycles=1, samples=5)
    assert result["x"][0] == 2
    assert abs(result["x"][-1] - 2) < 1e-6
    assert result["period"] > 6


def test_launch_that_does_not_rise_stays_at_the_origin():
    for angle in (0, -45):
        result = projectile(10, angle, gravity=10)
        assert result["time_of_flight"] == 0
        assert result["range"] == 0
        assert result["max_height"] == 0
        assert result["x"][-1] == 0 and result["y"][-1] == 0


def test_motion_replaces_non_finite_samples_with_null():
    result = motion("t", "log(t)", [0, 1], samples=5)
    assert result["y"][0] is None
    assert any(value is not None for value in result["y"])
    json.dumps(result, allow_nan=False)


def test_static_file_rejects_a_prefix_sibling(tmp_path):
    root = tmp_path / "demo"
    root.mkdir()
    page = root / "index.html"
    page.write_text("ok", encoding="utf-8")
    sibling = tmp_path / "demo-backup"
    sibling.mkdir()
    secret = sibling / "secret.html"
    secret.write_text("no", encoding="utf-8")
    assert _demo().safe_static(root, "/../demo-backup/secret.html") is None
    assert _demo().safe_static(root, "/index.html") == page.resolve()


def test_physics_result_keeps_the_facts_and_drops_the_samples():
    from desmos_mcp.worker import render_physics

    result = render_physics(
        {
            "scenario": "projectile",
            "speed": 20,
            "angle_degrees": 45,
            "gravity": 10,
            "rendering": {"default_width": 300, "default_height": 200, "samples": 200},
        }
    )
    assert set(result) == {"png", "warnings", "scenario", "facts"}
    assert result["facts"]["range"] == 40
    assert result["png"].startswith("iVBOR")

