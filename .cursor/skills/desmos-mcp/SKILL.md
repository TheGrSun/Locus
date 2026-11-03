---
name: desmos-mcp
description: >-
  Plot and analyze functions with the Desmos MCP server: offline 2D PNG,
  offline z=f(x,y) surfaces, symbolic y=f(x) analysis, and editable Desmos 2D
  or 3D pages. Use when the user asks to graph, plot, visualize, compare, or
  analyze a formula, surface, slider, implicit curve, or Desmos graph, including
  三维, 曲面, 函数图像, and official Desmos demos.
---

# Desmos MCP

The server is a local stdio MCP process. Offline plots and the official Desmos demos need no API key. A key is only for loading your expressions into the local HTML page.

## Route

| Request | Tool | Syntax |
| --- | --- | --- |
| Check y=f(x) | `validate_formula` | `y = sin(x)`, `2*x` |
| Several curves and their analysis in one result | `explore_functions` | explicit `*`, radians, `pi` |
| Picture only, up to 12 curves | `plot_multiple_functions` | same offline syntax |
| Domain, derivative, corners | `analyze_formula` | same offline syntax |
| 1–6 surfaces together | `plot_3d_surface` | `formulas: ["z = x^2 + y^2", "z = x"]` |
| Data points, optional curve or surface | `plot_points` | `[[0, 0], [1, 1]]` or `[[0, 0, 1], [1, 1, 2]]` |
| Parametric curve in t | `plot_parametric` | `x: "cos(t)", y: "sin(t)", z: "t"` |
| 2D vector field | `plot_vector_field` | `fx: "-y", fy: "x"` |
| Projectile, oscillator, or x(t), y(t) | `simulate_physics` | `scenario: "projectile"`, `speed: 20`, `angle_degrees: 45` |
| Derivative or tangent on one curve | `plot_math_function` | `show_derivative: true`, `tangent_at: 1` |
| Sliders, implicit, inequalities, edit | `create_interactive_graph` | Desmos LaTeX |

`dimension` is `2d` (`GraphingCalculator`) or `3d` (`Calculator3D`). 3D LaTeX looks like `["a=1", "z=a(x^2+y^2)"]`. Do not send `*` or `**` to the interactive tool. Do not send `\sin` or `z=` to the offline 2D tools. `plot_3d_surface` returns one x, y, z view in the chat. It does not rotate.

Offline piecewise uses Python conditions: `x^2 if x < 0 else x`. Parametric components use `t`, not `x`. Vector components use `x` and `y`.

Interactive LaTeX can also express a slider (`a=1`), an implicit curve (`x^2+y^2=9`), an inequality (`y>x`), and a point (`(1,2)`). Do not send `if/else` or `*` to the interactive tool.

There is no symbolic integral, limit, or 3D analysis tool. Say so if asked.

## Official demos

Stable API is **v1.12**. These URLs returned HTTP 200:

- 2D parabola: https://www.desmos.com/api/v1.12/docs/examples/parabola.html
- 3D calculator: https://www.desmos.com/api/v1.12/docs/examples/3d.html
- Docs: https://www.desmos.com/api/v1.12/docs/index.html and https://www.desmos.com/api/v1.12/docs/3d.html

https://www.desmos.com/api/v1.11/docs/examples/3d.html returns **404**. Do not link it. v1.13 is not stable until Spring 2027.

The official 3D demo is a blank `Calculator3D`. The official 2D demo loads `y=x^2`. Both open without the user's API key. A key is only for loading expressions into the local HTML. Never copy a key out of Desmos's demo HTML.

## What to tell the user

1. State the window you used. Default `[-10, 10]` only when the user did not specify one.
2. PNG results are already inline images. Mention warnings and that the curve or surface is sampled.
3. For HTML, give `path` and `official_demo` first. The official demo needs no API key. Mention https://www.desmos.com/my-api only if the user wants those expressions loaded in the local file. Browser edits do not sync back.
4. Suggest one next experiment: a parameter, a derivative, or the other dimension.

Read `resources://guide` and `resources://official-demos` if a tool result conflicts with this skill. The tool result wins.
