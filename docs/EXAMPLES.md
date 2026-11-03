# Tool examples / 工具示例

These are MCP tool arguments, not shell commands. 以下是 MCP 工具参数，不是终端命令。

## Offline graph

`plot_math_function`:

```json
{"formula":"y = sin(x)","x_range":[-6.283185307,6.283185307],"y_range":[-1.5,1.5]}
```

Ranges are numeric: convert `pi` to a number for range arguments. Formula text can contain `pi`.
坐标范围需要数字，公式文本可使用 `pi`。

`plot_multiple_functions`:

```json
{"formulas":["x^2","2*x+1"],"x_range":[-3,3],"y_range":[-3,10]}
```

The result includes a legend, structured metadata as text, and native `image/png` content.

## Symbolic analysis

`analyze_formula`:

```json
{"formula":"x^3-3*x","analysis_type":"detailed"}
```

Expect real domain, real range, derivative `3*x**2 - 3`, and stationary points `{-1, 1}`.
Use `abs(x)` with `critical_points` to see why a corner can matter even when it is not a stationary point.
Returned warnings explain incomplete differentiability or symbolic solving.

## Interactive sliders and curves

`create_interactive_graph`:

```json
{"expressions":["a=1","y=a x^2","x^2+y^2=9"],"title":"Explore a parabola and circle","language":"en","x_range":[-6,6],"y_range":[-4,8]}
```

Use `"language":"zh-CN"` for Chinese interface guidance.
For trigonometry, Desmos LaTeX in JSON is `"y=\\sin(x)"`; JSON needs two backslashes to encode one.
The offline syntax `sin(x)` and the interactive LaTeX syntax `\\sin(x)` should not be mixed automatically.

Open `path` in a browser, supply your key, then move the `a` slider or edit expressions.
“Save state JSON” downloads Desmos's opaque state; “Import state” reloads it. “Reset” restores the original graph.
“Export PNG” saves the current view. The original HTML is unchanged by browser edits.

## Several curves and their analysis

`explore_functions` returns one PNG and one analysis object per formula:

```json
{"formulas":["sin(x)","cos(x)"],"x_range":[-6.283185307,6.283185307],"y_range":[-1.5,1.5],"analysis_type":"detailed"}
```

`plot_multiple_functions` draws up to 12 curves when the analysis is not needed.

## Several surfaces

`plot_3d_surface` accepts `formulas` so the surfaces share one view:

```json
{"formulas":["z = x^2 + y^2","z = 0"],"x_range":[-2,2],"y_range":[-2,2],"z_range":[0,8]}
```

A single `formula` argument still works. Pass `z_range` when the picture should use a fixed vertical scale. To orbit or zoom, open the live demo or `create_interactive_graph` with `dimension` `3d`.

## Points, parametric curves, vectors, and tangents

`plot_points` draws data. Add `formula` to overlay `y=f(x)` or, for `[x, y, z]` points, `z=f(x,y)`.

```json
{"points":[[0,0],[1,1],[2,4]],"formula":"x^2","x_range":[-1,3]}
```

`plot_parametric` uses `t`. Include `z` for a space curve.

```json
{"x":"cos(t)","y":"sin(t)","z":"t","t_range":[0,6.283185307]}
```

`plot_vector_field` draws direction arrows. Components use `x` and `y`.

```json
{"fx":"-y","fy":"x","x_range":[-2,2],"y_range":[-2,2],"density":12}
```

Piecewise formulas use Python conditions, including inside the tools above: `x^2 if x < 0 else x`.
`plot_math_function` accepts `show_derivative: true` and `tangent_at: 1` to draw those lines on the same axes.

## Offline surface

`plot_3d_surface`:

```json
{"formula":"z = sin(x)*cos(y)","x_range":[-6.283185307,6.283185307],"y_range":[-6.283185307,6.283185307],"z_range":[-1.2,1.2]}
```

The PNG is a sampled surface. It is not a symbolic 3D analysis. Keep explicit `*`.

## Interactive 3D

`create_interactive_graph` with `"dimension":"3d"`:

```json
{"expressions":["a=1","z=a(x^2+y^2)"],"title":"Paraboloid","language":"zh-CN","dimension":"3d"}
```

The page constructs `Desmos.Calculator3D` and links the official v1.12 demos. Drag to orbit. The official 3D demo starts blank; this page loads the expressions after the user connects with their own key.

## Official demos

Verified on 2026-11-02:

| Page | Result |
| --- | --- |
| https://www.desmos.com/api/v1.12/docs/examples/parabola.html | HTTP 200. `GraphingCalculator` and `y=x^2`. |
| https://www.desmos.com/api/v1.12/docs/examples/3d.html | HTTP 200. Blank `Calculator3D`. |
| https://www.desmos.com/api/v1.11/docs/examples/3d.html | HTTP 404. Do not link it. |

v1.12 is the current stable production API. v1.13 is not stable until Spring 2027.

## Guided prompts

`basic_graphing_assistant` arguments: `{"formula":"sin(x)"}`.

`advanced_math_analysis` arguments: `{"formula":"x^3-3*x","analysis_focus":"derivatives"}`.

The assistant should explain axes and assumptions, inspect warnings, and suggest a concrete next experiment.
For missing ranges, use [-10,10] unless the user's goal requires clarification.
