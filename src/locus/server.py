"""MCP tools, resources, and prompts. The stdio channel is reserved for MCP."""

import argparse
import asyncio
import base64
import json
import math
import sys
from typing import Annotated, Literal
from uuid import uuid4

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ImageContent, TextContent
from pydantic import Field

from . import __version__
from .config import Settings, load_settings
from .formulas import FUNCTIONS, looks_like_surface, parse_formula, validate_range

Formula = Annotated[str, Field(min_length=1, max_length=500)]
FormulaList = Annotated[list[Formula], Field(min_length=1, max_length=12)]
SurfaceList = Annotated[list[Formula], Field(min_length=1, max_length=6)]
Bounds = Annotated[list[float], Field(min_length=2, max_length=2)]
AnalysisType = Literal["basic", "detailed", "critical_points"]

GUIDE = """Locus workflow.
1. Several y=f(x) curves plus analysis in ONE result: explore_functions.
   The PNG and each formula's analysis return together. Syntax: x^2, y = sin(x), 2*x, pi. Radians.
   plot_multiple_functions is the same shared-axes picture without analysis. Up to 12 curves.
2. Several z=f(x,y) surfaces on one view: plot_3d_surface with formulas.
   Syntax: z = sin(x)*cos(y). The PNG is one x, y, z view and does not rotate.
   There is no symbolic 3D analysis tool.
3. Domain, range, and derivatives of y=f(x): analyze_formula. Explain warnings.
   Stationary points are not necessarily extrema; nondifferentiable candidates may also matter.
4. Otherwise start with [-10, 10] and say so. Suggest one next experiment.
5. Images are native MCP PNG content. Paths are on the SERVER machine.
   Static graphs are finite samples; narrow the window near gaps or rapid oscillation.
6. Physics motion: simulate_physics. projectile uses speed, angle_degrees and gravity. oscillator uses amplitude and angular_frequency. motion uses x(t) and y(t). The result is the trajectory plus time of flight, range, height, or period. No air resistance.
7. Also offline: piecewise `x^2 if x < 0 else x`; plot_points for [x, y] or [x, y, z] data;
   plot_parametric for x(t), y(t), optional z(t); plot_vector_field for fx(x,y) and fy(x,y).
   plot_math_function can set show_derivative or tangent_at. Write multiplication as *.
"""


async def run_worker(payload: dict, timeout: float) -> dict:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "locus.worker",
        payload["operation"],
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    ready = False
    try:
        assert process.stdin and process.stdout and process.stderr
        process.stdin.write(json.dumps(payload).encode())
        await process.stdin.drain()
        process.stdin.close()

        # A cold macOS runner may spend tens of seconds importing Matplotlib and
        # creating its font cache. That setup is not part of the calculation budget.
        ready_line = await asyncio.wait_for(process.stdout.readline(), max(60.0, timeout))
        try:
            worker_ready = json.loads(ready_line) == {"ready": True}
        except (json.JSONDecodeError, UnicodeDecodeError):
            worker_ready = False
        if not worker_ready:
            stderr = await process.stderr.read()
            await process.wait()
            detail = ""
            try:
                message = json.loads(ready_line)
            except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
                message = None
            if isinstance(message, dict) and message.get("error"):
                detail = str(message["error"])
            elif ready_line:
                detail = ready_line.decode(errors="replace").strip()[:500]
            stderr_text = stderr.decode(errors="replace").strip()[-500:]
            raise ToolError("Calculation worker did not initialize correctly. " + (detail or stderr_text))
        ready = True
        stdout, _stderr, _returncode = await asyncio.wait_for(
            asyncio.gather(process.stdout.read(), process.stderr.read(), process.wait()), timeout
        )
    except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
        if process.returncode is None:
            process.kill()
        await process.communicate()
        if isinstance(exc, asyncio.CancelledError):
            raise
        if ready:
            message = f"Calculation exceeded {timeout:g}s. Simplify the formula or use basic analysis."
        else:
            message = "Calculation worker initialization exceeded its startup timeout."
        raise ToolError(message) from exc
    if process.returncode:
        raise ToolError("Calculation process failed. Try a simpler expression or reduce the plotting range.")
    result = json.loads(stdout)
    if "error" in result:
        raise ToolError(result["error"])
    return result["result"]


def _save_png(cfg: Settings, prefix: str, png: str) -> str | None:
    if not cfg.rendering.save_files:
        return None
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.output_dir / f"{prefix}_{uuid4().hex}.png"
    path.write_bytes(base64.b64decode(png))
    return str(path.resolve())


def create_server(settings: Settings | None = None) -> FastMCP:
    cfg = settings if settings is not None else load_settings()
    mcp = FastMCP("locus", instructions=GUIDE)
    worker_slots = asyncio.Semaphore(2)

    async def calculate(payload: dict):
        async with worker_slots:
            return await run_worker(payload, cfg.timeout_seconds)

    @mcp.resource("resources://info")
    def info() -> dict:
        return {
            "name": "locus",
            "version": __version__,
            "offline_png": True,
            "offline_3d": True,
            "guide": "resources://guide",
        }

    @mcp.resource("resources://guide")
    def guide() -> str:
        return GUIDE

    @mcp.resource("resources://examples")
    def examples() -> dict:
        return {
            "offline": ["y = x^2", "sin(x)", "exp(-x^2)*cos(3*x)", "1/x", "abs(x)"],
            "surfaces": ["z = x^2 + y^2", "sin(x)*cos(y)"],
            "functions": sorted(FUNCTIONS),
        }

    @mcp.prompt("basic_graphing_assistant")
    def basic_prompt(formula: str = "x^2") -> str:
        """Start a guided plotting conversation with a formula or a description."""
        return f"Help me explore this formula: {formula}\n{GUIDE}\nRespond in my language, explain the axes, and suggest one experiment."

    @mcp.prompt("advanced_math_analysis")
    def advanced_prompt(formula: str = "x^3-3*x", analysis_focus: str = "derivatives") -> str:
        """Guide symbolic analysis and verify its interpretation with a plot."""
        return (
            f"Analyze {formula}, focusing on {analysis_focus}. Use the supported tools; distinguish exact results "
            "from sampled plots and unresolved symbolic results. Plot the function and, when useful, its derivative. "
            "Do not claim integration, limit, or symbolic 3D tools exist.\n" + GUIDE
        )

    @mcp.prompt("visualize_3d")
    def visualize_3d_prompt(formula: str = "z=x^2+y^2") -> str:
        """Guide a 3D surface and return one sampled PNG."""
        return (
            f"Explore this 3D surface: {formula}. "
            "If it uses explicit * and variables x,y, call plot_3d_surface and describe the sampled image. "
            "Do not claim symbolic 3D analysis exists.\n" + GUIDE
        )

    @mcp.tool()
    def validate_formula(formula: Formula) -> dict:
        """Check offline y=f(x) syntax. Returns repair guidance without requiring client sampling."""
        try:
            expr = parse_formula(formula)
            return {"valid": True, "normalized": str(expr), "syntax": "offline", "next_tool": "plot_math_function"}
        except ValueError as exc:
            result = {"valid": False, "error": str(exc), "examples": ["y = x^2", "2*x + 1", "sin(x)"]}
            if looks_like_surface(formula):
                result["next_tool"] = "plot_3d_surface"
                result["examples"] = ["z = x^2 + y^2", "sin(x)*cos(y)"]
            return result

    @mcp.tool()
    async def analyze_formula(ctx: Context, formula: Formula, analysis_type: AnalysisType = "basic") -> dict:
        """Analyze a real function of x. Detailed adds range and derivative; critical_points includes corner candidates."""
        await ctx.report_progress(0, 1, "Analyzing formula")
        result = await calculate({"operation": "analyze", "formula": formula, "analysis_type": analysis_type})
        await ctx.report_progress(1, 1, "Analysis complete")
        return result

    async def plot(
        ctx: Context,
        formulas: list[str],
        x_range,
        y_range,
        use_api: bool = False,
        show_derivative: bool = False,
        tangent_at: float | None = None,
    ):
        try:
            xs = validate_range(x_range, (-10, 10))
            ys = validate_range(y_range)
            if tangent_at is not None and (isinstance(tangent_at, bool) or not math.isfinite(tangent_at)):
                raise ValueError("tangent_at is the x value where the tangent line is drawn, for example 1.")
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        await ctx.report_progress(0, 2, "Rendering offline PNG")
        result = await calculate(
            {
                "operation": "render",
                "formulas": formulas,
                "x_range": xs,
                "y_range": ys,
                "show_derivative": show_derivative,
                "tangent_at": tangent_at,
                "rendering": cfg.rendering.model_dump(),
            }
        )
        metadata = {"backend": "matplotlib", "formulas": formulas, "x_range": xs, "warnings": result["warnings"]}
        if use_api:
            metadata["warnings"].append(
                "use_api is deprecated and ignored. Plots are rendered locally."
            )
        if cfg.rendering.save_files:
            cfg.output_dir.mkdir(parents=True, exist_ok=True)
            path = cfg.output_dir / f"plot_{uuid4().hex}.png"
            path.write_bytes(base64.b64decode(result["png"]))
            metadata["path"] = str(path.resolve())
        await ctx.report_progress(2, 2, "Plot ready")
        return [
            TextContent(type="text", text=json.dumps(metadata)),
            ImageContent(type="image", data=result["png"], mimeType="image/png"),
        ]

    @mcp.tool()
    async def plot_math_function(
        ctx: Context,
        formula: Formula,
        x_range: Bounds | None = None,
        y_range: Bounds | None = None,
        use_api: bool = False,
        show_derivative: bool = False,
        tangent_at: float | None = None,
    ) -> list[TextContent | ImageContent]:
        """Plot y=f(x) offline and return a native PNG. Set show_derivative or tangent_at to overlay those lines.

        Piecewise syntax is x^2 if x < 0 else x. use_api is deprecated. Defaults x to [-10, 10].
        """
        result = await plot(ctx, [formula], x_range, y_range, use_api, show_derivative, tangent_at)
        if show_derivative or tangent_at is not None:
            metadata = json.loads(result[0].text)
            overlays = []
            if show_derivative:
                overlays.append("derivative")
            if tangent_at is not None:
                overlays.append(f"tangent at {tangent_at:g}")
            metadata["overlays"] = overlays
            result[0] = TextContent(type="text", text=json.dumps(metadata))
        return result

    @mcp.tool()
    async def plot_multiple_functions(
        ctx: Context, formulas: FormulaList, x_range: Bounds | None = None, y_range: Bounds | None = None
    ) -> list[TextContent | ImageContent]:
        """Compare 1–12 offline formulas on shared axes, with a legend and native PNG output."""
        return await plot(ctx, formulas, x_range, y_range)

    @mcp.tool()
    async def explore_functions(
        ctx: Context,
        formulas: FormulaList,
        x_range: Bounds | None = None,
        y_range: Bounds | None = None,
        analysis_type: AnalysisType = "basic",
        show_derivative: bool = False,
        tangent_at: float | None = None,
    ) -> list[TextContent | ImageContent]:
        """Plot 1–12 y=f(x) formulas together and return each analysis in the same result as the PNG.

        Use this when the model should see the curves and their domains or derivatives without another call.
        Syntax uses explicit *: ["sin(x)", "cos(x)"]. Piecewise: x^2 if x < 0 else x.
        detailed adds range and derivative; critical_points adds corners.
        show_derivative and tangent_at draw extra lines on the same axes.
        """
        try:
            xs = validate_range(x_range, (-10, 10))
            ys = validate_range(y_range)
            if tangent_at is not None and (isinstance(tangent_at, bool) or not math.isfinite(tangent_at)):
                raise ValueError("tangent_at is the x value where the tangent line is drawn, for example 1.")
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        await ctx.report_progress(0, 2, "Analyzing and plotting formulas")
        result = await calculate(
            {
                "operation": "explore",
                "formulas": formulas,
                "analysis_type": analysis_type,
                "x_range": xs,
                "y_range": ys,
                "show_derivative": show_derivative,
                "tangent_at": tangent_at,
                "rendering": cfg.rendering.model_dump(),
            }
        )
        metadata = {
            "backend": "matplotlib",
            "formulas": formulas,
            "x_range": xs,
            "analyses": result["analyses"],
            "warnings": result["warnings"],
        }
        overlays = []
        if show_derivative:
            overlays.append("derivative")
        if tangent_at is not None:
            overlays.append(f"tangent at {tangent_at:g}")
        if overlays:
            metadata["overlays"] = overlays
        saved = _save_png(cfg, "explore", result["png"])
        if saved:
            metadata["path"] = saved
        await ctx.report_progress(2, 2, "Exploration ready")
        return [
            TextContent(type="text", text=json.dumps(metadata)),
            ImageContent(type="image", data=result["png"], mimeType="image/png"),
        ]

    def _surfaces(formula: str | None, formulas: list[str] | None) -> list[str]:
        if formula and formulas:
            raise ToolError("Pass formula or formulas, not both.")
        if formulas:
            return list(formulas)
        if formula:
            return [formula]
        raise ToolError("Provide formula or formulas, for example ['z = x^2 + y^2', 'z = x'].")

    async def _surfaces_image(
        ctx: Context,
        formulas: list[str],
        x_range: list[float],
        y_range: list[float],
        z_range: list[float] | None,
        progress: str,
    ) -> list[TextContent | ImageContent]:
        await ctx.report_progress(0, 2, progress)
        result = await calculate(
            {
                "operation": "render3d",
                "formulas": formulas,
                "x_range": x_range,
                "y_range": y_range,
                "z_range": z_range,
                "rendering": cfg.rendering.model_dump(),
            }
        )
        metadata = {
            "backend": "matplotlib",
            "dimension": "3d",
            "formulas": formulas,
            "x_range": x_range,
            "y_range": y_range,
            "warnings": result["warnings"],
            "interaction": "One view of the standard x, y, z axes. The picture does not rotate.",
        }
        if z_range is not None:
            metadata["z_range"] = z_range
        saved = _save_png(cfg, "surface", result["png"])
        if saved:
            metadata["path"] = saved
        await ctx.report_progress(2, 2, "Surface ready")
        return [
            TextContent(type="text", text=json.dumps(metadata)),
            ImageContent(type="image", data=result["png"], mimeType="image/png"),
        ]

    @mcp.tool()
    async def plot_3d_surface(
        ctx: Context,
        formula: Formula | None = None,
        formulas: SurfaceList | None = None,
        x_range: Bounds | None = None,
        y_range: Bounds | None = None,
        z_range: Bounds | None = None,
    ) -> list[TextContent | ImageContent]:
        """Plot 1–6 surfaces z=f(x,y) together and return one native PNG. Example formulas: ['z = x^2 + y^2', 'z = x'].

        A single formula argument still works. This is one sampled view, not symbolic 3D analysis.
        Orbit and zoom are in the local demo page.
        """
        try:
            chosen = _surfaces(formula, formulas)
            xs = validate_range(x_range, (-10, 10))
            ys = validate_range(y_range, (-10, 10))
            zs = validate_range(z_range)
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        return await _surfaces_image(ctx, chosen, xs, ys, zs, "Rendering offline 3D PNG")

    async def _picture(ctx: Context, operation: str, payload: dict, prefix: str, progress: str):
        await ctx.report_progress(0, 2, progress)
        result = await calculate({"operation": operation, **payload, "rendering": cfg.rendering.model_dump()})
        metadata = {key: value for key, value in result.items() if key != "png"}
        metadata["backend"] = "matplotlib"
        saved = _save_png(cfg, prefix, result["png"])
        if saved:
            metadata["path"] = saved
        await ctx.report_progress(2, 2, "Plot ready")
        return [
            TextContent(type="text", text=json.dumps(metadata)),
            ImageContent(type="image", data=result["png"], mimeType="image/png"),
        ]

    def _checked_points(points: list[list[float]]) -> list[list[float]]:
        if not 1 <= len(points) <= 400:
            raise ValueError("Provide 1 to 400 points.")
        widths = {len(point) for point in points}
        if widths not in ({2}, {3}):
            raise ValueError("Use all [x, y] points or all [x, y, z] points, with finite coordinates.")
        checked = []
        for point in points:
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 1e6 for value in point):
                raise ValueError("Point coordinates must be finite and within [-1e6, 1e6].")
            checked.append([float(value) for value in point])
        return checked

    @mcp.tool()
    async def plot_points(
        ctx: Context,
        points: Annotated[list[list[float]], Field(min_length=1, max_length=400)],
        formula: Formula | None = None,
        x_range: Bounds | None = None,
        y_range: Bounds | None = None,
    ) -> list[TextContent | ImageContent]:
        """Plot 1–400 data points and return one PNG. Each point is [x, y] or [x, y, z].

        An optional formula is drawn with the points: y=f(x) for 2D points, z=f(x,y) for 3D points.
        Offline syntax uses explicit *. Example: points [[0, 0], [1, 1], [2, 4]] and formula x^2.
        """
        try:
            checked = _checked_points(points)
            xs = validate_range(x_range)
            ys = validate_range(y_range)
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        return await _picture(
            ctx,
            "points",
            {"points": checked, "formula": formula, "x_range": xs, "y_range": ys},
            "points",
            "Plotting data points",
        )

    @mcp.tool()
    async def plot_parametric(
        ctx: Context,
        x: Formula,
        y: Formula,
        z: Formula | None = None,
        t_range: Bounds | None = None,
    ) -> list[TextContent | ImageContent]:
        """Plot a parametric curve in t and return one PNG. 2D uses x(t), y(t). 3D also uses z(t).

        Example: x cos(t), y sin(t), z t, t_range [0, 6.283185307]. Write multiplication as *.
        Omit z for a plane curve. This is sampled, not a symbolic arc-length analysis.
        """
        try:
            ts = validate_range(t_range, (0, 6.283185307179586))
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        return await _picture(
            ctx,
            "parametric",
            {"x": x, "y": y, "z": z, "t_range": ts},
            "parametric",
            "Plotting parametric curve",
        )

    @mcp.tool()
    async def plot_vector_field(
        ctx: Context,
        fx: Formula,
        fy: Formula,
        x_range: Bounds | None = None,
        y_range: Bounds | None = None,
        density: Annotated[int, Field(ge=6, le=24)] = 15,
    ) -> list[TextContent | ImageContent]:
        """Plot the 2D vector field (fx, fy) as arrows and return one PNG. fx and fy use x and y.

        Example: fx -y, fy x. density is the number of arrows along each axis, from 6 to 24.
        Arrows are drawn at unit length so direction stays visible where the magnitude changes.
        """
        try:
            xs = validate_range(x_range, (-4, 4))
            ys = validate_range(y_range, (-4, 4))
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        return await _picture(
            ctx,
            "vector",
            {"fx": fx, "fy": fy, "x_range": xs, "y_range": ys, "density": density},
            "vector",
            "Plotting vector field",
        )

    @mcp.tool()
    async def simulate_physics(
        ctx: Context,
        scenario: Literal["projectile", "oscillator", "motion"] = "projectile",
        speed: float = 20,
        angle_degrees: float = 45,
        gravity: float = 9.81,
        amplitude: float = 1,
        angular_frequency: float = 2,
        phase: float = 0,
        cycles: Annotated[float, Field(ge=0.25, le=8)] = 2,
        x: Formula | None = None,
        y: Formula | None = None,
        t_range: Bounds | None = None,
    ) -> list[TextContent | ImageContent]:
        """Simulate a physics trajectory and return the path image plus the measured facts.

        projectile: launch from the origin, y up, no drag. A launch that does not rise stays at the origin.
        oscillator: x = A cos(omega t + phase), for cycles periods.
        motion: positions x(t) and y(t), for example x = t and y = 4*t - 4.9*t^2. Write multiplication as *.
        """
        try:
            ts = validate_range(t_range, (0, 2))
            if scenario == "motion" and (not x or not y):
                raise ValueError("motion needs x(t) and y(t), for example x = t and y = 4*t - 4.9*t^2.")
        except ValueError as exc:
            raise ToolError(str(exc)) from exc
        return await _picture(
            ctx,
            "physics",
            {
                "scenario": scenario,
                "speed": speed,
                "angle_degrees": angle_degrees,
                "gravity": gravity,
                "amplitude": amplitude,
                "angular_frequency": angular_frequency,
                "phase": phase,
                "cycles": cycles,
                "x": x,
                "y": y,
                "t_range": ts,
            },
            "physics",
            "Simulating motion",
        )

    return mcp


def main():
    parser = argparse.ArgumentParser(description="Locus: plot a formula from the chat.")
    parser.add_argument("--config", help="Path to a JSON configuration file")
    args = parser.parse_args()
    try:
        server = create_server(load_settings(args.config))
    except (OSError, ValueError) as exc:
        parser.error(f"Invalid configuration: {exc}")
    server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
