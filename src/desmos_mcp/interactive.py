"""Generate a standalone page using the documented Desmos browser SDK."""

import json
from importlib.resources import files

# v1.12 is the current stable production API. v1.13 is not stable until Spring 2027.
# The v1.11 docs link examples/3d.html, and that URL returns HTTP 404.
API_VERSION = "v1.12"
DEMO_2D = f"https://www.desmos.com/api/{API_VERSION}/docs/examples/parabola.html"
DEMO_3D = f"https://www.desmos.com/api/{API_VERSION}/docs/examples/3d.html"
DOCS_2D = f"https://www.desmos.com/api/{API_VERSION}/docs/index.html"
DOCS_3D = f"https://www.desmos.com/api/{API_VERSION}/docs/3d.html"


def make_page(
    expressions: list[str],
    title: str,
    x_range: list[float],
    y_range: list[float],
    language: str,
    dimension: str = "2d",
) -> str:
    data = json.dumps(
        {
            "expressions": expressions,
            "title": title,
            "xRange": x_range,
            "yRange": y_range,
            "language": language,
            "dimension": dimension,
            "apiVersion": API_VERSION,
            "officialDemos": {"2d": DEMO_2D, "3d": DEMO_3D},
        },
        ensure_ascii=True,
    )
    # Do not let an expression or title terminate the inline script element.
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = files("desmos_mcp").joinpath("graph.html").read_text(encoding="utf-8")
    template = (
        template.replace("__API_VERSION__", API_VERSION)
        .replace("__DEMO_2D__", DEMO_2D)
        .replace("__DEMO_3D__", DEMO_3D)
        .replace("__DOCS_2D__", DOCS_2D)
        .replace("__DOCS_3D__", DOCS_3D)
    )
    return template.replace("__GRAPH_DATA__", data)
