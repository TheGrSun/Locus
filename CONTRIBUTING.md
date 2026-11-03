# Contributing

Install dependencies with `uv sync --locked`. Run `uv run pytest`, `uv run ruff check src tests`, and `uv build` before submitting changes.
Use Node.js 22+ to run `node --test tests/bounds.test.cjs tests/i18n.test.cjs`.

- `server.py`: MCP contracts, errors, progress, resources, prompts and worker lifecycle.
- `formulas.py`: the offline syntax whitelist and mathematical input validation.
- `worker.py`: computation and headless plotting in disposable processes.
- `config.py`: configuration discovery, defaults and validation.
- Do not commit `.cursor`, log files, local agent notes, or a personal Nix setup.

Keep user expressions out of Python eval/exec. Do not add `print` to the MCP process's stdout; it carries protocol messages.
Worker stdout is an internal JSON channel. Do not put secrets in generated artifacts.

Cover changed observable behavior: valid/invalid formula inputs, native image output, symbolic edge cases, timeouts,
CLI stdio communication. Deterministic tests should not call external services.

Keep both READMEs and the migration notes consistent when changing tool arguments, defaults or return types.
Do not invent REST endpoints.
