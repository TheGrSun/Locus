"""Disposable calculation process. stdout contains one JSON response only."""

import base64
import io
import json
import sys
import warnings

import sympy as sp
from sympy.calculus.util import continuous_domain, function_range

from .formulas import T, X, Y, parse_component, parse_formula, parse_surface
from .physics import motion, oscillator, projectile


def analyze(formula: str, analysis_type: str) -> dict:
    expr = parse_formula(formula)
    result = {"formula": formula, "normalized": str(expr), "variable": "x", "warnings": []}
    domain = None
    try:
        domain = continuous_domain(expr, X, sp.S.Reals)
        result["domain"] = str(domain)
    except (NotImplementedError, ValueError) as exc:
        result["warnings"].append(f"Domain could not be determined: {exc}")
    if analysis_type == "detailed" and domain is not None:
        try:
            result["range"] = str(function_range(expr, X, domain))
        except (NotImplementedError, ValueError) as exc:
            result["warnings"].append(f"Range could not be determined: {exc}")
    if analysis_type in ("detailed", "critical_points"):
        derivative = sp.diff(expr, X)
        result["derivative"] = str(derivative)
        search_domain = domain if domain is not None else sp.S.Reals
        stationary = None
        try:
            stationary = sp.solveset(derivative, X, domain=search_domain)
            if stationary.has(sp.ConditionSet):
                result["warnings"].append("The stationary-point equation is unresolved; this is not an empty set.")
        except (NotImplementedError, ValueError) as exc:
            result["warnings"].append(f"Stationary points could not be determined: {exc}")
        try:
            differentiable_domain = continuous_domain(derivative, X, sp.S.Reals)
            candidates = search_domain - differentiable_domain
        except (NotImplementedError, ValueError):
            candidates = sp.S.EmptySet
            for term in expr.atoms(sp.Abs):
                candidates |= sp.solveset(term.args[0], X, domain=search_domain)
            result["warnings"].append("Differentiability was not fully resolved; corner candidates may be incomplete.")
        # SymPy assigns sign(0)=0, but abs(x) has no derivative at zero.
        # Conversely abs(x^2) IS differentiable there. Check finite candidate sets
        # with the difference quotient before calling any point stationary.
        if isinstance(candidates, sp.FiniteSet) and len(candidates) <= 12:
            for point in list(candidates):
                try:
                    quotient = (expr - expr.subs(X, point)) / (X - point)
                    left = sp.limit(quotient, X, point, dir="-")
                    right = sp.limit(quotient, X, point, dir="+")
                    if left.is_finite is True and right.is_finite is True and left == right:
                        candidates -= sp.FiniteSet(point)
                except (NotImplementedError, ValueError):
                    result["warnings"].append(f"Could not verify differentiability at {point}.")
        result["nondifferentiable_candidates"] = str(candidates)
        if stationary is not None:
            result["stationary_points"] = str(stationary - candidates)
    return result


def render(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib.figure import Figure

    cfg = payload["rendering"]
    fig = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    ax = fig.subplots()
    x = np.linspace(*payload["x_range"], cfg["samples"])
    messages = []

    def sample_curve(expr):
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)
            values = np.asarray(sp.lambdify(X, expr, modules="numpy")(x), dtype=complex)
            values = np.broadcast_to(values, x.shape)
            y = np.where(np.isfinite(values) & (np.abs(values.imag) < 1e-10), values.real, np.nan).copy()
        finite = y[np.isfinite(y)]
        if finite.size:
            span = (
                np.diff(payload["y_range"])[0]
                if payload["y_range"]
                else max(float(np.percentile(finite, 95) - np.percentile(finite, 5)), 1)
            )
            jumps = np.flatnonzero(np.abs(np.diff(y)) > 5 * span)
            y[jumps] = np.nan
            y[jumps + 1] = np.nan
        return y

    ax.set_prop_cycle(color=["#4f86c6", "#d16b66", "#5aa57a", "#8a6bb8", "#e09a4a", "#6e767d"])
    for formula in payload["formulas"]:
        expr = parse_formula(formula)
        y = sample_curve(expr)
        if not np.isfinite(y).any():
            messages.append(f"{formula}: no finite real values in this interval.")
        ax.plot(x, y, label=formula, linewidth=2)
        if payload.get("show_derivative"):
            ax.plot(x, sample_curve(sp.diff(expr, X)), linestyle="--", linewidth=1.5, label=f"d/dx ({formula})")
        if payload.get("tangent_at") is not None:
            point = float(payload["tangent_at"])
            height = _finite_real(expr.subs(X, point))
            slope = _finite_real(sp.diff(expr, X).subs(X, point))
            if height is None or slope is None:
                messages.append(f"{formula}: tangent at {point:g} is not a finite real number.")
            else:
                ax.plot(x, sample_curve(height + slope * (X - point)), linestyle=":", linewidth=1.8, label=f"tangent at {point:g}")
    ax.set(xlim=payload["x_range"], xlabel="x", ylabel="y")
    if payload["y_range"]:
        ax.set_ylim(payload["y_range"])
    ax.axhline(0, color="#b24a45", linewidth=1.05)
    ax.axvline(0, color="#3f6f9e", linewidth=1.05)
    ax.grid(alpha=0.2)
    ax.legend(loc="best")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig.clear()
    return {"png": base64.b64encode(buf.getvalue()).decode("ascii"), "warnings": messages}


SURFACE_COLORS = ("#4f86c6", "#d16b66", "#5aa57a", "#e09a4a", "#8a6bb8", "#6e767d")


def _sampled_surface(expr, x_grid, y_grid):
    import numpy as np

    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        values = np.asarray(sp.lambdify((X, Y), expr, modules="numpy")(x_grid, y_grid), dtype=complex)
        values = np.broadcast_to(values, x_grid.shape)
        return np.where(np.isfinite(values) & (np.abs(values.imag) < 1e-10), values.real, np.nan).copy()


def _standard_axes(ax, x_range, y_range, z_range):
    """One oblique view of the x, y, z axes. z is up."""
    ax.set(xlim=x_range, ylim=y_range, zlim=z_range, xlabel="x", ylabel="y", zlabel="z")
    ax.view_init(elev=30, azim=-60)
    ax.plot(x_range, [0, 0], [0, 0], color="#d6453d", linewidth=1.25)
    ax.plot([0, 0], y_range, [0, 0], color="#2c6cb5", linewidth=1.25)
    ax.plot([0, 0], [0, 0], z_range, color="#2e9a5a", linewidth=1.25)
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_facecolor((1, 1, 1, 0))
    ax.grid(True)


def render_surface(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.ticker as ticker
    import mpl_toolkits.mplot3d  # noqa: F401  (registers the 3d projection)
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    cfg = payload["rendering"]
    formulas = payload.get("formulas") or [payload["formula"]]
    parsed = [(formula, parse_surface(formula)) for formula in formulas]
    grid = max(40, min(80, int(cfg["samples"]) // 20))
    fig = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    ax = fig.add_subplot(projection="3d")
    xs = np.linspace(*payload["x_range"], grid)
    ys = np.linspace(*payload["y_range"], grid)
    x_grid, y_grid = np.meshgrid(xs, ys)
    messages = ["One view of the standard x, y, z coordinate system. This is not a symbolic 3D analysis."]
    sheets = []
    finite_z = []
    for ordinal, (formula, expr) in enumerate(parsed):
        z = _sampled_surface(expr, x_grid, y_grid)
        finite = z[np.isfinite(z)]
        if finite.size:
            finite_z.append(finite)
        else:
            messages.append(f"{formula}: no finite real values in this window.")
        sheets.append((ordinal, formula, z))
    if payload.get("z_range"):
        z_range = payload["z_range"]
    elif finite_z:
        stacked = np.concatenate(finite_z)
        low, high, mid = (float(item) for item in np.percentile(stacked, [10, 90, 50]))
        cap = max(float(payload["x_range"][1] - payload["x_range"][0]), float(payload["y_range"][1] - payload["y_range"][0]), 4.0)
        if not high > low or high - low > cap * 2:
            low, high = mid - cap, mid + cap
        z_range = [low - 1, high + 1] if low == high else [low, high]
    else:
        z_range = [-1.0, 1.0]
    handles = []
    for ordinal, formula, z in sheets:
        if not payload.get("z_range"):
            z = np.where((z >= z_range[0]) & (z <= z_range[1]), z, np.nan)
            limit = max((z_range[1] - z_range[0]) * 0.2, 1e-6)
            steep = np.zeros(z.shape, dtype=bool)
            steep[:-1, :] |= np.abs(np.diff(z, axis=0)) > limit
            steep[1:, :] |= np.abs(np.diff(z, axis=0)) > limit
            steep[:, :-1] |= np.abs(np.diff(z, axis=1)) > limit
            steep[:, 1:] |= np.abs(np.diff(z, axis=1)) > limit
            z = np.where(steep, np.nan, z)
        style = {"linewidth": 0, "antialiased": True, "alpha": 0.72}
        if len(parsed) == 1:
            style["cmap"] = "viridis"
        else:
            style["color"] = SURFACE_COLORS[ordinal % len(SURFACE_COLORS)]
            handles.append(Line2D([0], [0], color=style["color"], lw=4))
        ax.plot_surface(x_grid, y_grid, z, **style)
    _standard_axes(ax, payload["x_range"], payload["y_range"], z_range)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_major_locator(ticker.MaxNLocator(4))
    ax.set_title(parsed[0][0] if len(parsed) == 1 else "surfaces", fontsize=11)
    if handles:
        ax.legend(handles, [formula for formula, _expr in parsed], loc="upper left", fontsize=8)
    try:
        fig.tight_layout()
    except ValueError:
        pass
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig.clear()
    return {
        "png": base64.b64encode(buf.getvalue()).decode("ascii"),
        "warnings": messages,
    }


def explore(payload: dict) -> dict:
    analyses = [analyze(formula, payload["analysis_type"]) for formula in payload["formulas"]]
    rendered = render(payload)
    return {"png": rendered["png"], "warnings": rendered["warnings"], "analyses": analyses}


def _finite_real(value) -> float | None:
    import math

    try:
        number = complex(sp.N(value))
    except (TypeError, ValueError):
        return None
    if abs(number.imag) > 1e-8 or not math.isfinite(number.real):
        return None
    return float(number.real)


def _components(expressions, symbol, samples, t_range):
    import numpy as np

    t = np.linspace(*t_range, samples)
    coords = []
    for expr in expressions:
        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)
            values = np.asarray(sp.lambdify(symbol, expr, modules="numpy")(t), dtype=complex)
            values = np.broadcast_to(values, t.shape)
            coords.append(np.where(np.isfinite(values) & (np.abs(values.imag) < 1e-10), values.real, np.nan).copy())
    return coords


def _pad_span(values) -> list[float]:
    import numpy as np

    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return [-1.0, 1.0]
    low, high = float(finite.min()), float(finite.max())
    if low == high:
        return [low - 1, high + 1]
    pad = 0.05 * (high - low)
    return [low - pad, high + pad]


def render_points(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib.figure import Figure

    cfg = payload["rendering"]
    points = payload["points"]
    dimension = 3 if len(points[0]) == 3 else 2
    fig = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    messages = []
    coords = [np.array([point[axis] for point in points], dtype=float) for axis in range(dimension)]
    if dimension == 2:
        ax = fig.subplots()
        x_range = payload.get("x_range") or _pad_span(coords[0])
        y_range = payload.get("y_range")
        if payload.get("formula"):
            xs = np.linspace(*x_range, cfg["samples"])
            with warnings.catch_warnings(), np.errstate(all="ignore"):
                warnings.simplefilter("ignore", RuntimeWarning)
                values = np.asarray(sp.lambdify(X, parse_formula(payload["formula"]), modules="numpy")(xs), dtype=complex)
                values = np.broadcast_to(values, xs.shape)
                curve = np.where(np.isfinite(values) & (np.abs(values.imag) < 1e-10), values.real, np.nan)
            ax.plot(xs, curve, color="#1f77b4", linewidth=2, label=payload["formula"])
            ax.legend(loc="best")
        ax.scatter(coords[0], coords[1], color="#d62728", zorder=3)
        ax.set(xlim=x_range, xlabel="x", ylabel="y")
        if y_range:
            ax.set_ylim(y_range)
        ax.axhline(0, color="#b24a45", linewidth=1.05)
        ax.axvline(0, color="#3f6f9e", linewidth=1.05)
        ax.grid(alpha=0.2)
    else:
        import mpl_toolkits.mplot3d  # noqa: F401

        ax = fig.add_subplot(projection="3d")
        ax.scatter(coords[0], coords[1], coords[2], color="#d62728")
        if payload.get("formula"):
            grid = max(30, min(50, int(cfg["samples"]) // 30))
            x_range = payload.get("x_range") or _pad_span(coords[0])
            y_range = payload.get("y_range") or _pad_span(coords[1])
            xs = np.linspace(*x_range, grid)
            ys = np.linspace(*y_range, grid)
            x_grid, y_grid = np.meshgrid(xs, ys)
            z = _sampled_surface(parse_surface(payload["formula"]), x_grid, y_grid)
            ax.plot_surface(x_grid, y_grid, z, cmap="viridis", linewidth=0, alpha=0.45, antialiased=True)
        else:
            x_range = payload.get("x_range") or _pad_span(coords[0])
            y_range = payload.get("y_range") or _pad_span(coords[1])
        _standard_axes(ax, x_range, y_range, _pad_span(coords[2]))
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig.clear()
    return {"png": base64.b64encode(buf.getvalue()).decode("ascii"), "warnings": messages, "dimension": f"{dimension}d"}


def render_parametric(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    cfg = payload["rendering"]
    expressions = [parse_component(payload["x"]), parse_component(payload["y"])]
    if payload.get("z"):
        expressions.append(parse_component(payload["z"]))
    coords = _components(expressions, T, cfg["samples"], payload["t_range"])
    fig = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    if len(coords) == 3:
        import mpl_toolkits.mplot3d  # noqa: F401

        ax = fig.add_subplot(projection="3d")
        ax.plot(coords[0], coords[1], coords[2], linewidth=2)
        _standard_axes(ax, _pad_span(coords[0]), _pad_span(coords[1]), _pad_span(coords[2]))
        dimension = "3d"
    else:
        ax = fig.subplots()
        ax.plot(coords[0], coords[1], linewidth=2)
        ax.set(xlabel="x", ylabel="y")
        ax.axhline(0, color="#b24a45", linewidth=1.05)
        ax.axvline(0, color="#3f6f9e", linewidth=1.05)
        ax.grid(alpha=0.2)
        try:
            ax.set_aspect("equal", adjustable="datalim")
        except (ValueError, NotImplementedError):
            pass
        dimension = "2d"
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig.clear()
    messages = []
    if not any(np_any(coord) for coord in coords):
        messages.append("No finite real points in this t interval.")
    return {"png": base64.b64encode(buf.getvalue()).decode("ascii"), "warnings": messages, "dimension": dimension}


def np_any(values) -> bool:
    import numpy as np

    return bool(np.isfinite(values).any())


def render_vector(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib.figure import Figure

    cfg = payload["rendering"]
    density = int(payload["density"])
    fig = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    ax = fig.subplots()
    xs = np.linspace(*payload["x_range"], density)
    ys = np.linspace(*payload["y_range"], density)
    x_grid, y_grid = np.meshgrid(xs, ys)
    horizontal = _sampled_surface(parse_surface(payload["fx"]), x_grid, y_grid)
    vertical = _sampled_surface(parse_surface(payload["fy"]), x_grid, y_grid)
    magnitude = np.hypot(horizontal, vertical)
    valid = np.isfinite(magnitude) & (magnitude > 1e-12)
    spacing = min((payload["x_range"][1] - payload["x_range"][0]) / density, (payload["y_range"][1] - payload["y_range"][0]) / density)
    unit_x = np.where(valid, horizontal / magnitude, np.nan)
    unit_y = np.where(valid, vertical / magnitude, np.nan)
    ax.quiver(x_grid, y_grid, unit_x, unit_y, angles="xy", scale_units="xy", scale=1.6 / spacing, color="#225c45")
    ax.set(xlim=payload["x_range"], ylim=payload["y_range"], xlabel="x", ylabel="y")
    ax.grid(alpha=0.2)
    try:
        ax.set_aspect("equal", adjustable="box")
    except (ValueError, NotImplementedError):
        pass
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    fig.clear()
    messages = []
    if not valid.any():
        messages.append("The vector field has no finite nonzero values in this window.")
    return {"png": base64.b64encode(buf.getvalue()).decode("ascii"), "warnings": messages}


def render_physics(payload: dict) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import numpy as np
    from matplotlib.figure import Figure

    scenario = payload["scenario"]
    if scenario == "projectile":
        sampled = projectile(payload["speed"], payload["angle_degrees"], payload.get("gravity", 9.81))
    elif scenario == "oscillator":
        sampled = oscillator(
            payload["amplitude"], payload["angular_frequency"], payload.get("phase", 0.0), payload.get("cycles", 2.0)
        )
    else:
        sampled = motion(payload["x"], payload["y"], payload["t_range"])
    cfg = payload["rendering"]
    figure = Figure(figsize=(cfg["default_width"] / 100, cfg["default_height"] / 100), dpi=100)
    axes = figure.subplots()
    xs = np.array([np.nan if value is None else value for value in sampled["x"]], dtype=float)
    ys = np.array([np.nan if value is None else value for value in sampled["y"]], dtype=float)
    finite = np.isfinite(xs) & np.isfinite(ys)
    axes.plot(xs, ys, color="#4f86c6", linewidth=2.4)
    if finite.any():
        first = int(np.flatnonzero(finite)[0])
        axes.scatter([xs[first]], [ys[first]], color="#d07a76", zorder=3)
    axes.axhline(0, color="#b24a45", linewidth=1.05)
    axes.axvline(0, color="#3f6f9e", linewidth=1.05)
    axes.set(xlabel="x", ylabel="y")
    axes.grid(alpha=0.2)
    try:
        axes.set_aspect("equal", adjustable="datalim")
    except (ValueError, NotImplementedError):
        pass
    figure.tight_layout()
    buf = io.BytesIO()
    figure.savefig(buf, format="png")
    figure.clear()
    facts = {key: value for key, value in sampled.items() if key not in {"time", "x", "y"}}
    warnings = []
    if not finite.any():
        warnings.append("No finite real points in this motion.")
    return {
        "png": base64.b64encode(buf.getvalue()).decode("ascii"),
        "warnings": warnings,
        "scenario": sampled["scenario"],
        "facts": facts,
    }


def warm_render_backend(three_d: bool = False):
    """Force one-time Matplotlib font discovery before the calculation timer."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    figure = Figure(figsize=(1, 1), dpi=20)
    if three_d:
        import mpl_toolkits.mplot3d  # noqa: F401
        import numpy as np

        axes = figure.add_subplot(projection="3d")
        grid = np.zeros((2, 2))
        axes.plot_surface(grid, grid, grid)
        axes.set(xlabel="x", ylabel="y", zlabel="z")
    else:
        axes = figure.subplots()
        axes.plot([0, 1], [0, 1], label="warmup")
        axes.set(xlabel="x", ylabel="y")
        axes.legend()
    figure.savefig(io.BytesIO(), format="png")
    figure.clear()


def main():
    try:
        operation = sys.argv[1]
        if operation in ("render", "render3d", "explore", "points", "parametric", "vector", "physics"):
            # Font discovery happens on the first actual draw rather than import.
            # Complete one throwaway draw before announcing worker readiness.
            warm_render_backend(three_d=operation in ("render3d", "parametric"))
        print(json.dumps({"ready": True}), flush=True)
        payload = json.load(sys.stdin)
        operations = {
            "analyze": lambda item: analyze(item["formula"], item["analysis_type"]),
            "render3d": render_surface,
            "explore": explore,
            "points": render_points,
            "parametric": render_parametric,
            "vector": render_vector,
            "physics": render_physics,
        }
        result = operations.get(operation, render)(payload)
        print(json.dumps({"result": result}, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}))


if __name__ == "__main__":
    main()
