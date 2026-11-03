# Changelog

## 0.3.0 (unreleased)

- Add `explore_functions`, returning several y=f(x) curves and each analysis in one tool result.
- `plot_3d_surface` accepts `formulas` and draws up to six surfaces on one view.
- `plot_3d_surface` is one sampled view. Orbit and zoom stay on the local page.
- Physics results return the measured facts with the picture. The sample columns stay on the server.
- Add offline piecewise `if/else`, `plot_points`, `plot_parametric`, and `plot_vector_field`.
- `plot_math_function` can overlay the derivative and a tangent line.
- Add offline `plot_3d_surface` for sampled `z=f(x,y)` PNG images.
- Remove the interactive page, official example links, and API key entry.
- Publish the `visualize_3d` prompt.

## 0.2.0 (unreleased)

- Fix FastMCP progress reporting and return native PNG image content.
- Add a packaged CLI and retain `uv run src/main.py` compatibility.
- Replace the assumed REST endpoint with standalone HTML using the official Desmos JavaScript SDK.
- Add interactive setup guidance, expression editing, sliders, reset, PNG export and JSON state import/export.
- Validate configuration and inputs; build expressions through a restricted AST parser rather than `sympify` on user input.
- Run analysis and rendering in disposable processes with timeout, cancellation cleanup and bounded active concurrency.
- Exclude cold worker imports and Matplotlib font-cache setup from the calculation timeout on CI runners.
- Distinguish stationary points, nondifferentiable candidates and unresolved symbolic results.
- Add guide/example resources, working prompts, regression tests and CI.

### Migration from 0.1

Replace `config.json` with the new README example: the unused `desmos` settings block is removed.
`DESMOS_API_KEY` is no longer used by Python; interactive pages accept your key directly in the browser.
The obsolete `use_api` tool parameter is temporarily accepted but emits a warning; offline PNG is always local.
`validate_formula` and `analyze_formula` now return structured objects; plotting returns text plus image content.
Prompt arguments are flat (`formula`, `analysis_focus`) rather than nested `args`.
The demonstration `hello` tool is removed. Default files no longer go to the desktop.
The project is pinned to the FastMCP 2.x API family; upgrade the major version deliberately.
