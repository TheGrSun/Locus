# Client setup / 客户端接入

Use an MCP client that supports local stdio servers. It launches this process and communicates via stdin/stdout.
服务器由客户端启动，使用标准输入输出通信。

## Copyable configuration

For clients accepting `mcpServers` JSON (for example Claude Desktop):

```json
{
  "mcpServers": {
    "locus": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/Locus", "run", "--locked", "locus", "--config", "/ABSOLUTE/PATH/Locus/config.json"]
    }
  }
}
```

Replace **both** repository paths. On Windows use an absolute path such as `C:\\Projects\\Locus` inside JSON.
For clients using another configuration format, copy the same command and argument array into its stdio server settings.
JSON 的两个仓库路径都需要替换；使用其他配置格式的客户端时，保留相同 command 和 args 即可。

If a GUI client cannot find `uv`, use the absolute executable path from `command -v uv` (macOS/Linux)
or `where uv` (Windows). Do not rely on the GUI inheriting your terminal PATH.

## Check the connection

1. Run `uv run locus --help` from the repository. It should print CLI help.
2. Restart/reconnect the client; inspect its tool list for the tools in the README.
3. Call `validate_formula` with `{"formula":"y = x^2"}`; expect `valid: true`.
4. Call `plot_math_function` with `{"formula":"sin(x)"}`; expect text metadata and native image content.
5. If the client cannot display images, open the saved PNG path on the server machine.

## Troubleshooting / 常见问题

| Symptom / 现象 | Resolution / 处理 |
| --- | --- |
| Command not found | Run `uv sync --locked`; use an absolute `uv` path in the client. |
| Server waits silently in the terminal | Normal stdio behavior; use an MCP client, not interactive typing. |
| Invalid configuration | Replace the old `desmos` block; verify JSON and supported settings in README. |
| `2x` or LaTeX fails offline | Write `2*x` and `sin(x)`. |
| Calculation timeout | Simplify the formula, use `basic` analysis, or deliberately raise the configured timeout. |
| Local file cannot be opened by remote client | Transfer it from the server; local paths are not public share links. |

Sampling and elicitation are not required. Guidance is available through resources and prompts, so clients without
those optional callbacks still receive useful syntax errors and tool results.
无需客户端支持 LLM sampling 或 elicitation，基础绘图和错误指导即可使用。
