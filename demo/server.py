"""Compute a graph from the expression the user just submitted."""

import json
import math
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import sympy as sp

from locus.formulas import X, Y, looks_like_surface, parse_formula, parse_surface, validate_range
from locus.worker import warm_render_backend

ROOT = Path(__file__).parent.resolve()


def _numbers(values) -> list[float | None]:
    cleaned: list[float | None] = []
    for value in np.ravel(np.asarray(values, dtype=float)):
        number = float(value)
        cleaned.append(round(number, 5) if math.isfinite(number) else None)
    return cleaned


def _sample(expr, symbol, axis):
    function = sp.lambdify(symbol, expr, modules="numpy")
    with np.errstate(all="ignore"):
        values = function(*axis) if isinstance(symbol, tuple) else function(axis)
        values = np.asarray(values, dtype=float)
        shape = np.shape(axis[0] if isinstance(symbol, tuple) else axis)
        return np.broadcast_to(values, shape)


def _formulas(body: dict) -> list[str]:
    lines = [line.strip() for line in str(body.get("formulas") or "").splitlines()]
    formulas = [line for line in lines if line]
    if not formulas:
        raise ValueError("请输入至少一条公式。")
    if len(formulas) > 6:
        raise ValueError("一次最多 6 条公式。")
    return formulas


def _range(body: dict, key: str, default: tuple[float, float]) -> list[float]:
    value = body.get(key)
    if value in (None, "", []):
        return validate_range(None, default)
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("范围需要两个数字。")
    try:
        bounds = [float(value[0]), float(value[1])]
    except (TypeError, ValueError):
        raise ValueError("范围需要两个数字。") from None
    return validate_range(bounds)


def safe_static(root: Path, url_path: str) -> Path | None:
    base = root.resolve()
    requested = url_path.split("?", 1)[0]
    relative = "index.html" if requested == "/" else requested.lstrip("/")
    file = (base / relative).resolve()
    if not file.is_relative_to(base) or file.suffix not in {".html", ".js"} or not file.is_file():
        return None
    return file


def _parsed_lines(formulas, parser, surface_hint=False):
    parsed = []
    errors = []
    for index, formula in enumerate(formulas, start=1):
        try:
            parsed.append((formula, parser(formula)))
        except ValueError as exc:
            if surface_hint and looks_like_surface(formula):
                detail = "这是曲面公式，请切换到三维曲面。"
            else:
                detail = str(exc)
            errors.append(f"第 {index} 行「{formula}」：{detail}")
    if not parsed and errors:
        raise ValueError("\n".join(errors))
    return parsed, errors


def compute(body: dict) -> dict:
    mode = body.get("mode")
    if mode == "curves":
        formulas = _formulas(body)
        x_range = _range(body, "xRange", (-6.283185307, 6.283185307))
        y_range = _range(body, "yRange", (-4, 4))
        xs = np.linspace(*x_range, 900)
        series = []
        parsed, errors = _parsed_lines(formulas, parse_formula, surface_hint=True)
        for formula, expr in parsed:
            series.append({"name": formula, "y": _numbers(_sample(expr, X, xs))})
            if body.get("derivative"):
                series.append({"name": f"d/dx ({formula})", "y": _numbers(_sample(sp.diff(expr, X), X, xs)), "dash": True})
        return {"kind": "xy", "x": _numbers(xs), "series": series, "xRange": x_range, "yRange": y_range, "warning": "\n".join(errors)}
    if mode == "surfaces":
        formulas = _formulas(body)
        x_range = _range(body, "xRange", (-6, 6))
        y_range = _range(body, "yRange", (-6, 6))
        xs = np.linspace(*x_range, 42)
        ys = np.linspace(*y_range, 42)
        x_grid, y_grid = np.meshgrid(xs, ys)
        surfaces = []
        parsed, errors = _parsed_lines(formulas, parse_surface)
        for formula, expr in parsed:
            z = _sample(expr, (X, Y), (x_grid, y_grid))
            surfaces.append({"name": formula, "z": [_numbers(row) for row in z]})
        return {"kind": "surface", "x": _numbers(xs), "y": _numbers(ys), "surfaces": surfaces, "warning": "\n".join(errors)}
    raise ValueError("未知的计算类型。")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        file = safe_static(ROOT, self.path)
        if file is None:
            self.send_error(404)
            return
        data = file.read_bytes()
        mime = "text/javascript; charset=utf-8" if file.suffix == ".js" else "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/compute":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > 1_000_000:
            payload = {"error": "请求体不能超过 1 MB。"}
            status = 413
        else:
            try:
                payload = compute(json.loads(self.rfile.read(length) or b"{}"))
                status = 200
            except json.JSONDecodeError:
                payload = {"error": "请求不是合法的 JSON。"}
                status = 400
            except ValueError as exc:
                payload = {"error": str(exc)}
                status = 400
            except Exception:
                payload = {"error": "无法计算这个输入。"}
                status = 400
        try:
            data = json.dumps(payload, allow_nan=False).encode()
        except ValueError:
            data = json.dumps({"error": "无法计算这个输入。"}).encode()
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(fmt % args)


if __name__ == "__main__":
    warm_render_backend()
    host = os.environ.get("LOCUS_DEMO_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, 8766), Handler)
    print(f"http://{host}:8766", flush=True)
    server.serve_forever()
