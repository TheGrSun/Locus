# Locus

[English](README.md) · [客户端接入](docs/CLIENTS.md) · [调用示例](docs/EXAMPLES.md)

在对话里画出公式。想拖动时，再放进 Desmos。
安装命令是 `uv run locus`，仓库是 [Locus](https://github.com/TheGrSun/Locus)。
Python 3.10+ · FastMCP 2.x · Apache-2.0 · 独立开源项目，非 Desmos 官方产品。

## 可以做什么

| 工具 | 结果 | 使用条件 |
| --- | --- | --- |
| `validate_formula` | 标准化公式，或返回可操作的修正建议 | 离线 |
| `plot_math_function` | 原生 PNG 图片及可选的保存路径 | 离线 |
| `plot_multiple_functions` | 同一坐标系比较 1–12 个函数 | 离线 |
| `explore_functions` | 这些曲线和每个公式的分析，一次返回 | 离线 |
| `plot_3d_surface` | 同一视角下 1–6 个 `z = f(x, y)` 采样曲面 | 离线 |
| `plot_points` | 二维或三维散点，可叠加一条公式 | 离线 |
| `plot_parametric` | 参数曲线 `x(t), y(t)` 或再加 `z(t)` | 离线 |
| `plot_vector_field` | 平面向量场 `(fx, fy)` 的箭头 | 离线 |
| `simulate_physics` | 抛体、简谐振动，或自定义 `x(t)`、`y(t)`，并给出轨迹 | 离线 |
| `analyze_formula` | 定义域；可进一步计算值域、导数、驻点和不可导候选点 | 离线 |
| `create_interactive_graph` | 独立 HTML，使用官方 v1.12 API：可编辑公式、滑块、缩放、导出 PNG、保存和导入 JSON 状态。链接的 Desmos 示例不需要 key。把这些公式载入本页时使用自己的 key | 浏览器和网络。个人 API key 可选，只有载入自己的公式时才需要 |

离线曲线工具使用 `y = x^2`、`2*x + 1`、`sin(x)`、`sqrt(x)`、`abs(x)` 等语法。
`plot_3d_surface` 可以画一个曲面，也可以用 `formulas` 同时画最多六个，都在同一个视角里。对话里的图不能旋转。旋转和缩放在下面的实时演示页或 Desmos 3D 页面里完成。
`explore_functions` 把多条 `y=f(x)` 画在一起，并在同一次结果里返回每条的分析。
交互工具使用 **Desmos LaTeX**，例如 `a=1`、`y=ax^2`、`x^2+y^2=9`，三维为 `z=a(x^2+y^2)`。
两种输入格式有明确区分；交互公式由连接后的 Desmos 计算器检查。

## 图长什么样

下面是离线工具直接画出的 PNG，不是 Desmos 页面的截图。实时演示页打开时，二维和三维都已经填好同一组叠加公式。

| 多条二维曲线 | 多张三维曲面 |
| --- | --- |
| ![正弦、衰减振荡和分段函数](docs/images/curves-overlay.png) | ![三张曲面叠在同一组 x、y、z 坐标上](docs/images/surfaces-overlay.png) |
| `sin(x)`、`exp(-x^2/8)*cos(2*x)`、`x^2/20 if x < 0 else sin(x)/x` | `sin(x)*cos(y)`、`exp(-(x^2+y^2)/8)`、`0.3*sin(2*x)+0.3*cos(2*y)` |

| 曲线 | 曲面 |
| --- | --- |
| ![sin(x) 与 cos(x)](docs/images/curves.png) | ![z = sin(x)*cos(y)](docs/images/surface.png) |
| `sin(x)` 与 `cos(x)` | `z = sin(x)*cos(y)`，一张 x、y、z 视图 |

| 散点 | 参数曲线 |
| --- | --- |
| ![落在 y = x^2 上的点](docs/images/points.png) | ![螺旋线 x=cos(t), y=sin(t), z=t](docs/images/parametric.png) |
| 点落在 `y = x^2` 上 | `x = cos(t)`，`y = sin(t)`，`z = t` |

| 向量场 | 抛体 |
| --- | --- |
| ![向量场 fx=-y, fy=x](docs/images/vector.png) | ![初速 20、仰角 45 度的抛体](docs/images/physics.png) |
| `fx = -y`，`fy = x` | 初速 20、仰角 45 度 |

## 助手会返回什么

离线绘图返回 **MCP 原生 PNG 图片内容**，同时返回公式、警告，以及启用保存时的文件路径等文本信息。
支持图片的客户端可直接在对话中显示图形。

交互绘图返回 **HTML 文件路径和资源 URI**，不是自动嵌入的浏览器会话。
需要在浏览器中打开文件，连接 Desmos 后编辑图表。客户端可以提供自己的预览界面，
但不是所有 MCP 客户端都会直接渲染 HTML 资源。本地文件 URI 也不是可公开分享的网址。

离线三维是采样曲面图。符号分析仍然只针对二维函数。
交互三维使用 Desmos API v1.12 的官方构造函数 `Desmos.Calculator3D`。

## 验证状态

0.2 在本地 macOS/Python 3.10 通过了 42 个 Python 测试和 3 个隔离的 JavaScript 控制器测试。另在独立安装的 wheel 中验证了命令入口、PNG 返回及 HTML 模板打包。
之后在 Linux / Python 3.11 上，`ruff check` 通过，47 个 pytest 测试通过，5 个 Node 控制器测试通过。
CI 已配置 Linux、macOS、Windows 和 Python 3.10/3.12；不表示远端所有任务已经运行通过。

HTML 控制器测试使用模拟 Desmos SDK。生成的二维和三维连接页已在浏览器中打开：页面会标明构造函数、初始公式，以及 v1.12 官方示例链接。官方三维示例会打开空白的 `Calculator3D`。尚未使用用户自己的 API key 完成一次真实连接。

## 安装并接入

先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后执行：

```sh
git clone https://github.com/TheGrSun/Locus.git
cd Locus
uv sync --locked
uv run locus --help
```

按[客户端接入文档](docs/CLIENTS.md)配置 MCP。手动启动命令：

```sh
uv run locus
```

启动后等待输入是正常现象：这是 stdio MCP 服务，需要客户端通过协议调用，不是终端聊天程序。
旧命令 `uv run src/main.py` 仍可使用。

接入后可以对助手说：

> 在 -2π 到 2π 上比较 sin(x) 和 cos(x)，解释它们的交点。

> 创建 a=1、y=ax^2 的交互图，用中文引导我观察参数变化。

> 画出 z = sin(x)*cos(y)，再给我一个可编辑的三维 Desmos 页面。

对话里直接返回图片。三维结果是一张 x、y、z 坐标轴的标准视图。
下面的官方示例在浏览器里打开即可，不需要 API key。

可编辑页面要打开返回的 HTML 文件。在 [Desmos](https://www.desmos.com/my-api) 申请自己的 key，填入页面后连接。Key 只留在页面内存里，用来加载官方 SDK；不会写入生成的 HTML，也不会出现在导出的状态 JSON 里。页面说明公式编辑、滑块、恢复初始图、导出图片，以及状态的保存和导入。不会自动打开浏览器。网页上的修改不会自动回到助手；关闭前请保存状态。

想自己拖动图像时，在仓库里运行：

```sh
uv run python demo/server.py
```

然后打开 http://127.0.0.1:8766。页面只在本机监听。

页面只有两种模式，打开时各自已经画好三条公式。三维是 `sin(x)*cos(y)`、`exp(-(x^2+y^2)/8)` 和 `0.3*sin(2*x)+0.3*cos(2*y)`，带 x、y、z 坐标轴。二维是 `sin(x)`、`exp(-x^2/8)*cos(2*x)` 和 `x^2/20 if x < 0 else sin(x)/x`。可以直接粘贴普通公式或 LaTeX，例如 `\sin(x)\cos(y)`、`x^{2}`。侧栏切换语言和模式，两种模式各自保留自己的公式。三维可以拖动旋转、滚轮缩放，按钮可以回到默认方向、从正上方看 XY，或放大缩小。二维曲线上这些按钮改的是坐标范围，还可以勾选画出导数。

页面链向已核实可打开的官方示例，对应稳定版 API **v1.12**：

- [二维抛物线示例](https://www.desmos.com/api/v1.12/docs/examples/parabola.html) 用 `GraphingCalculator` 载入 `y=x^2`。
- [三维示例](https://www.desmos.com/api/v1.12/docs/examples/3d.html) 是空白的 `Calculator3D`。
- [二维文档](https://www.desmos.com/api/v1.12/docs/index.html) 与 [三维文档](https://www.desmos.com/api/v1.12/docs/3d.html)。

`https://www.desmos.com/api/v1.11/docs/examples/3d.html` 返回 HTTP 404。v1.11 的三维文档虽然写了 `examples/3d.html`，该相对链接在 v1.11 上并不存在。v1.13 要到 2027 年春天才成为稳定生产版本。生成的页面不会复用 Desmos 官方示例 HTML 里的 API key。

## Agent harness

对外的路由是服务器说明、`resources://guide`、`resources://official-demos`，以及 `basic_graphing_assistant`、`advanced_math_analysis`、`visualize_3d` 这三个 prompt。[AGENTS.md](AGENTS.md) 是这套规则的短契约。`.cursor` 这类编辑器状态不放进仓库。

## 配置

优先级：`--config 路径` → `LOCUS_CONFIG` 环境变量 → 当前目录 `config.json` → 内置默认值。
相对输出路径以配置文件所在目录为基准。

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

没有配置文件时，文件保存在系统临时目录下的 `locus` 中；长期保存请指定输出目录。
文件名含 UUID，避免并发覆盖。`save_files=false` 只关闭 PNG 落盘，MCP 仍返回图片；交互 HTML 始终保存。
文件不会自动清理，可在输出目录手动删除不需要的图表。

公式长度、语法、坐标范围均有校验。绘图与符号计算在独立进程运行，超过时限会终止，同时最多运行两个计算进程。
白名单解析器不会执行输入中的 Python 代码。这是本地 stdio 服务，不是面向公开多租户环境的计算沙箱。

## 数学能力与边界

- 离线计算支持实变量 `x`，显式乘法及弧度制；常数包括 `pi`、`π`、`e`。
  函数包括 `sin/cos/tan`、`asin/acos/atan`、`sinh/cosh/tanh`、`exp`、`log/ln`、`sqrt`、`abs/Abs`。
- `basic` 计算定义域；`detailed` 增加值域和导数分析；`critical_points` 分别报告驻点和不可导候选点，不直接断言其为极值。
- 符号求解未完成时返回警告。`ConditionSet` 不代表无解；复杂计算可能超时。
- PNG 来自有限采样，间断点或高频振荡附近应缩小区间进一步检查。
- Desmos 官方提供[浏览器 JavaScript SDK v1.12](https://www.desmos.com/api/v1.12/docs/index.html)，没有使用假定的 REST 绘图接口。
  三维使用 [`Calculator3D`](https://www.desmos.com/api/v1.12/docs/3d.html)。离线工具不需要 key；只有在交互页面点击连接后才请求 SDK。
- 返回路径属于服务端机器。远程客户端需要另外传输文件，不能直接打开另一台机器的本地路径。
- 暂不提供符号积分、极限工具、三维符号分析，以及网页与 MCP 的自动状态同步。
  `plot_3d_surface` 只是 `z=f(x,y)` 的有限采样。

## 开发与迁移

```sh
uv sync --locked
uv run pytest
uv run ruff check src tests
node --test tests/interactive.test.cjs
uv build
```

Node.js 22+ 仅用于交互控制器的隔离测试，运行 MCP 服务不需要 Node。
参见[贡献指南](CONTRIBUTING.md)和 [0.2 迁移说明](CHANGELOG.md)。旧配置中的 `desmos` 块已移除，需要替换为上面的格式。
HTML 模板随 Python 包一起发布，安装 wheel 后可直接使用命令入口。

许可证：[Apache-2.0](LICENSE)。
