#!/usr/bin/env python3
"""Cursor harness hooks for Desmos MCP. Always prints one JSON object and exits 0."""

import json
import re
import sys

DEMO_2D = "https://www.desmos.com/api/v1.12/docs/examples/parabola.html"
DEMO_3D = "https://www.desmos.com/api/v1.12/docs/examples/3d.html"
OFFLINE = {"validate_formula", "plot_math_function", "plot_multiple_functions", "analyze_formula", "explore_functions"}
SURFACES = {"plot_3d_surface"}
DRAWINGS = SURFACES | {
    "explore_functions",
    "plot_points",
    "plot_parametric",
    "plot_vector_field",
    "plot_math_function",
    "plot_multiple_functions",
    "simulate_physics",
}
INTERACTIVE = {"create_interactive_graph"}

SESSION = f"""Desmos MCP harness
Route before calling a tool. Respond in the user's language.
- Several y=f(x) curves, with analysis in the same result: explore_functions. Up to 12. Syntax uses explicit *: sin(x), 2*x, pi. Radians.
- Several z=f(x,y) surfaces on one view: plot_3d_surface with formulas. Syntax: z = sin(x)*cos(y). The PNG is one x, y, z view. It does not rotate.
- Points: plot_points. Parametric x(t), y(t), z(t): plot_parametric. Vector field: plot_vector_field. Piecewise: x^2 if x < 0 else x. Derivative or tangent: plot_math_function show_derivative or tangent_at.
- Editable 2D graph: create_interactive_graph dimension 2d. Desmos LaTeX, not SymPy: ["a=1", "y=a x^2"].
- Editable 3D graph: create_interactive_graph dimension 3d. Desmos LaTeX: ["a=1", "z=a(x^2+y^2)"]. Constructor is Desmos.Calculator3D.
Stable API is v1.12. Official live demos: 2D {DEMO_2D} · 3D {DEMO_3D}. The v1.11 examples/3d.html URL returns HTTP 404. Do not link it.
Official demos open without the user's API key: use the 2D or 3D URL above. A key is only for loading their expressions into the local HTML file. Do not embed a key. Browser edits do not sync back.
Read .cursor/skills/desmos-mcp/SKILL.md when choosing a tool or explaining a result.
"""


def emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def load() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def tool_name(payload: dict) -> str:
    for key in ("tool_name", "tool", "name"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value.rsplit(":", 1)[-1]
    blob = json.dumps(payload, ensure_ascii=False)
    for name in (*OFFLINE, *SURFACES, *INTERACTIVE):
        if name in blob:
            return name
    return ""


def tool_args(payload: dict) -> dict:
    for key in ("tool_input", "arguments", "input", "params"):
        value = payload.get(key)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict):
            return value
    return {}


def formulas_of(args: dict) -> list[str]:
    found = []
    for key in ("formula", "formulas", "expressions", "x", "y", "z", "fx", "fy"):
        value = args.get(key)
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, list):
            found.extend(item for item in value if isinstance(item, str))
    return found


def offline_mismatch(item: str) -> bool:
    if "\\" in item:
        return True
    body = re.sub(r"^\s*y\s*=\s*", "", item.strip(), flags=re.IGNORECASE)
    return bool(re.match(r"z\s*=", body, flags=re.IGNORECASE) or re.search(r"(?<![A-Za-z])y(?![A-Za-z])", body))


def before_mcp(payload: dict) -> dict:
    name = tool_name(payload)
    args = tool_args(payload)
    texts = formulas_of(args)
    notes = []
    if name in OFFLINE and any(offline_mismatch(item) for item in texts):
        notes.append(
            "This looks like Desmos LaTeX or z=f(x,y). Use plot_3d_surface for z=f(x,y) with explicit *, "
            "or create_interactive_graph for LaTeX."
        )
    if name in SURFACES and any("\\" in item or "**" in item for item in texts):
        notes.append("plot_3d_surface uses offline syntax such as z = sin(x)*cos(y), not Desmos LaTeX.")
    if name in INTERACTIVE:
        dimension = args.get("dimension", "2d")
        joined = "\n".join(texts)
        if dimension != "3d" and "z=" in joined.replace(" ", "").lower():
            notes.append("These expressions assign z. Pass dimension 3d so the page uses Desmos.Calculator3D.")
        if any("*" in item for item in texts):
            notes.append("Interactive expressions are Desmos LaTeX. Write y=2x or z=x^2+y^2, not Python * or **.")
    result = {"permission": "allow"}
    if notes:
        result["agent_message"] = " ".join(notes) + f" Official demos: {DEMO_2D} and {DEMO_3D}."
    return result


def after_tool(payload: dict) -> dict:
    name = tool_name(payload)
    if name in INTERACTIVE or name in DRAWINGS:
        return {
            "additional_context": (
                "Tell the user what was drawn, the assumed window, and one next experiment. "
                "If the tool returned an HTML path, the official Desmos demo opens without an API key. "
                "A key is only for loading the user's expressions into that local file. Do not embed a key. "
                f"Link the matching official demo ({DEMO_2D} for 2D, {DEMO_3D} for 3D). "
                "Do not invent a public share link. Browser edits do not sync back. "
                "A 3D PNG is one x, y, z view, not a rotatable scene and not a symbolic result."
            )
        }
    return {}


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "session"
    payload = load()
    if mode == "session":
        emit({"additional_context": SESSION})
    elif mode == "before-mcp":
        emit(before_mcp(payload))
    elif mode == "after-tool":
        emit(after_tool(payload))
    else:
        emit({})


if __name__ == "__main__":
    main()
