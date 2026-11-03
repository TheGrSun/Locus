# Locus agent harness

This repository is the MCP server plus the Cursor harness that teaches an agent how to use it.

- Skill: `.cursor/skills/desmos-mcp/SKILL.md` — when to plot, which syntax, which official demo.
- Hooks: `.cursor/hooks.json` — session routing, a syntax warning before Desmos MCP calls, and a short reminder after 3D or interactive calls.
- Server instructions and `resources://guide` are the same routing rules for clients that are not Cursor.

Offline math and the official Desmos demos never need your own API key. A key is only for loading your expressions into the local HTML page. Do not embed a key in generated files.

Stable Desmos API: v1.12. The live demos are the parabola example and the 3D example under `https://www.desmos.com/api/v1.12/docs/examples/`. The v1.11 `examples/3d.html` URL returns 404.
