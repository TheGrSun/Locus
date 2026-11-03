import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".cursor" / "hooks" / "desmos_harness.py"


def run(mode: str, payload: dict | None = None) -> dict:
    completed = subprocess.run(
        [sys.executable, str(HOOK), mode],
        input=json.dumps(payload or {}),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_session_routes_and_names_live_demos():
    context = run("session")["additional_context"]
    assert "plot_3d_surface" in context
    assert "https://www.desmos.com/api/v1.12/docs/examples/parabola.html" in context
    assert "https://www.desmos.com/api/v1.12/docs/examples/3d.html" in context
    assert "404" in context
    assert "v1.11 examples/3d.html" in context


def test_before_mcp_allows_valid_calls_and_warns_on_mixed_syntax():
    allowed = run("before-mcp", {"tool_name": "plot_math_function", "tool_input": {"formula": "y = sin(x)"}})
    assert allowed == {"permission": "allow"}
    surface_on_2d = run("before-mcp", {"tool_name": "plot_math_function", "tool_input": {"formula": "z = x^2 + y^2"}})
    assert "plot_3d_surface" in surface_on_2d["agent_message"]
    warned = run("before-mcp", {"tool_name": "create_interactive_graph", "tool_input": {"expressions": ["y=2*x"]}})
    assert warned["permission"] == "allow"
    assert "LaTeX" in warned["agent_message"]
    surface = run(
        "before-mcp",
        {"tool_name": "MCP:desmos-mcp:create_interactive_graph", "arguments": {"expressions": ["z=x^2+y^2"]}},
    )
    assert "dimension 3d" in surface["agent_message"]


def test_after_tool_reminds_only_for_graphs():
    assert run("after-tool", {"tool_name": "validate_formula"}) == {}
    reminder = run("after-tool", {"tool_name": "plot_3d_surface"})["additional_context"]
    assert "official demo" in reminder
    assert "API key" in reminder
