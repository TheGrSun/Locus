# Desmos MCP

[中文](README.zh.md) · [Client setup](docs/CLIENTS.md) · [Examples](docs/EXAMPLES.md)

Give an AI assistant offline function plots and symbolic analysis, plus editable Desmos graphs in a browser.
Python 3.10+ · FastMCP 2.x · Apache-2.0 · Independent project, not affiliated with Desmos.

<a href="https://glama.ai/mcp/servers/@TheGrSun/Desmos-MCP">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@TheGrSun/Desmos-MCP/badge" alt="Desmos Server MCP server" />
</a>

## What works

| Tool | Result | Requirements |
| --- | --- | --- |
| `validate_formula` | Normalized formula or actionable syntax guidance | Offline |
| `plot_math_function` | PNG image and optional saved file | Offline |
| `plot_multiple_functions` | 1–12 curves on shared axes | Offline |
| `explore_functions` | Those curves plus each formula's analysis, in one result | Offline |
| `plot_3d_surface` | 1–6 sampled surfaces `z = f(x, y)` on one view | Offline |
| `plot_points` | Scatter data in 2D or 3D, with an optional formula | Offline |
| `plot_parametric` | Curve `x(t), y(t)` or `x(t), y(t), z(t)` | Offline |
| `plot_vector_field` | Arrows for a 2D field `(fx, fy)` | Offline |
| `simulate_physics` | Projectile, oscillator, or x(t), y(t), with the measured trajectory | Offline |
| `analyze_formula` | Domain; optionally range, derivative, stationary points and corner candidates | Offline |
| `create_interactive_graph` | Standalone HTML on the official v1.12 API: editable expressions, sliders, zoom, PNG export, and JSON state import/export. The linked Desmos demo opens with no key. Your own key loads these expressions into that local page | Browser and internet. A personal API key is optional, and required only to load your expressions |

Offline curve tools accept `y = x^2`, `2*x + 1`, `sin(x)`, `sqrt(x)`, `abs(x)`, `pi` and `e`.
`plot_3d_surface` accepts one surface, or `formulas` with up to six, on one view. The chat image does not rotate. Orbit and zoom are in the live demo below, or on the official Desmos 3D page.
`explore_functions` plots several `y=f(x)` curves and returns each analysis with that picture.
The interactive tool accepts **Desmos LaTeX**, including `a=1`, `y=ax^2`, `x^2+y^2=9`, and for 3D `z=a(x^2+y^2)`.
These are separate syntax contracts. Interactive expressions are checked by Desmos when the page connects.

## What the assistant returns

An offline plotting call returns **native MCP PNG image content** plus text metadata containing the formula,
warnings, and a saved file path when saving is enabled. Image-capable clients can show the plot directly in chat.

An interactive call returns **an HTML file path and resource URI**, not an embedded browser session.
Open the file in a browser to connect to Desmos and edit the graph. A client may offer its own preview UI,
but HTML resources are not automatically rendered by every MCP client. A local file URI is not a public share link.

Offline 3D is a sampled surface image. Symbolic analysis stays two-dimensional.
Interactive 3D uses the official `Desmos.Calculator3D` constructor from API v1.12.

## Verification status

The 0.2 release passed 42 Python tests and 3 isolated JavaScript controller tests locally on macOS/Python 3.10. The CLI, native PNG output, and bundled HTML template were also checked from a separately installed wheel.
Later local checks on Linux with Python 3.11: `ruff check` passed, 47 pytest tests passed, and 5 Node controller tests passed.
CI is configured for Linux, macOS and Windows with Python 3.10/3.12; this is not a claim that those remote jobs have passed.

The HTML controller tests simulate the Desmos SDK. The generated 2D and 3D setup screens were opened in a browser: each shows its constructor, the expressions, and the v1.12 demo links. The official 3D demo opens a blank `Calculator3D`. Loading a graph with a user-supplied API key was not exercised.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed, then:

```sh
git clone https://github.com/TheGrSun/Desmos-MCP.git
cd Desmos-MCP
uv sync --locked
uv run desmos-mcp --help
```

Connect your MCP client using the [copyable configuration](docs/CLIENTS.md). The server uses stdio:

```sh
uv run desmos-mcp
```

Waiting for input is normal: this command starts an MCP server, not a command-line chat.
The compatibility command `uv run src/main.py` also works.

Try asking your assistant:

> Plot sin(x) and cos(x) from -2*pi to 2*pi and explain where they cross.

> Create a Desmos graph with a=1 and y=ax^2 so I can explore the parameter.

> Plot z = sin(x)*cos(y) and then give me an editable 3D Desmos page.

The chat returns the picture directly. A 3D result is one view of the x, y, and z axes.
The official demos below open in a browser with no API key.

For an editable page, open the returned HTML file. Get your own key from [Desmos](https://www.desmos.com/my-api) and enter it on the page. The key stays in page memory and loads the official SDK. It is not embedded in the generated file and is not included in exported state JSON. The page explains editing, sliders, reset, PNG export, and saving or importing state. No browser opens automatically. Edits in the browser do not sync back to the assistant: save state before closing the page.

To drag a graph yourself, from this repository:

```sh
uv run python demo/server.py
```

Then open http://127.0.0.1:8766. The page listens on this machine only.

The page has two modes: a 2D curve and a 3D surface. Paste a plain formula or LaTeX such as `\sin(x)\cos(y)` or `x^{2}`. The sidebar switches language and mode. 3D opens with x, y, and z axes; drag to orbit, scroll to zoom, and use the buttons for the default view, a top-down XY view, or zoom. On a 2D curve those buttons change the window, and a checkbox can plot the derivative.

The page links the verified official demos for stable API **v1.12**:

- [2D parabola](https://www.desmos.com/api/v1.12/docs/examples/parabola.html) loads `y=x^2` with `GraphingCalculator`.
- [3D calculator](https://www.desmos.com/api/v1.12/docs/examples/3d.html) is a blank `Calculator3D`.
- [2D docs](https://www.desmos.com/api/v1.12/docs/index.html) and [3D docs](https://www.desmos.com/api/v1.12/docs/3d.html).

`https://www.desmos.com/api/v1.11/docs/examples/3d.html` returns HTTP 404, even though the v1.11 3D docs link to `examples/3d.html`. v1.13 is not the stable production API until Spring 2027. Generated pages do not reuse the API key embedded in Desmos's own demo HTML.

## Agent harness

Cursor loads three pieces when this repository is the project root:

| Piece | Role |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Short contract: which syntax, where the key goes, which demo is real |
| [.cursor/skills/desmos-mcp/SKILL.md](.cursor/skills/desmos-mcp/SKILL.md) | Skill the agent reads before choosing a tool |
| [.cursor/hooks.json](.cursor/hooks.json) | `sessionStart` injects the route; `beforeMCPExecution` warns on mixed syntax; `postToolUse` reminds the agent to hand back the file path and the official demo |

Other MCP clients get the same route from the server instructions, `resources://guide`, `resources://official-demos`, and the prompts `basic_graphing_assistant`, `advanced_math_analysis`, and `visualize_3d`.

## Configuration

Configuration priority: `--config PATH` → `DESMOS_MCP_CONFIG` → `./config.json` → built-in defaults.
Relative output directories resolve against the configuration file, not the caller's current directory.

```json
{
  "output_dir": "graphs",
  "timeout_seconds": 20,
  "rendering": {
    "default_width": 900,
    "default_height": 600,
    "samples": 1600,
    "save_files": true
  }
}
```

Without a configuration file, artifacts go to the operating system's temporary directory under `desmos-mcp`.
Use an explicit directory for lasting files. File names contain UUIDs. `save_files=false` disables saved PNGs;
interactive HTML is always saved because it is the result of that tool. Images still return as native MCP content.
Generated files are not automatically deleted. Delete unwanted artifacts from the configured output directory.

Offline inputs have length, syntax, and range limits. Symbolic analysis and rendering run in disposable processes
with a configurable timeout and at most two active workers. The whitelist parser never evaluates Python from user input.
This is a local stdio service, not a hardened public multi-tenant computation service.

## Accuracy and limits

- Offline analysis supports real-valued functions of `x` with explicit multiplication and radians.
  Allowed functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `exp`, `log`/`ln`, `sqrt`, `abs`/`Abs`.
- `basic` analyzes the domain. `detailed` adds range and derivative analysis. `critical_points` reports stationary points
  and possible nondifferentiable points separately. Candidates are not classified extrema.
- Unresolved symbolic results include warnings; a `ConditionSet` is not “no solutions.” Some requests can time out.
- Static PNG curves are sampled approximations; inspect a narrower range near discontinuities or rapid oscillations.
- Desmos's public integration is the [JavaScript SDK v1.12](https://www.desmos.com/api/v1.12/docs/index.html), not a REST PNG endpoint.
  3D uses [`Calculator3D`](https://www.desmos.com/api/v1.12/docs/3d.html). No API key is needed for offline tools.
  Requests to the SDK happen only after connecting in the browser.
- Returned file paths refer to the server machine. Remote clients need a separate file-transfer mechanism.
- Tools do not provide symbolic integration, limits, symbolic 3D analysis, or automatic browser-to-MCP state synchronization.
  `plot_3d_surface` is a finite sample of `z=f(x,y)`.

## Development

```sh
uv sync --locked
uv run pytest
uv run ruff check src tests
node --test tests/interactive.test.cjs
uv build
```

Node.js 22+ is needed only for the isolated interactive-controller tests, not for running the MCP server.
See [CONTRIBUTING.md](CONTRIBUTING.md) for module boundaries and validation requirements.
[CHANGELOG.md](CHANGELOG.md) documents the 0.2 migration, including removal of the old `desmos` configuration block.
The Python package includes the HTML template; the CLI works after wheel installation.

Licensed under [Apache-2.0](LICENSE).
