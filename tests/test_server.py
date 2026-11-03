import asyncio
import base64
import io
import json
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

from locus.config import Rendering, Settings, load_settings
from locus.server import create_server, run_worker


@pytest.fixture
def server(tmp_path):
    return create_server(Settings(output_dir=tmp_path, rendering=Rendering(default_width=600, default_height=400)))


async def test_guidance_prompts_and_validation(server):
    async with Client(server) as client:
        assert len(await client.list_tools()) == 10
        result = await client.call_tool("validate_formula", {"formula": "y=x^2"})
        assert result.data["valid"] is True
        invalid = await client.call_tool("validate_formula", {"formula": "2x"})
        assert invalid.data["valid"] is False and invalid.data["examples"]
        guide = await client.read_resource("resources://guide")
        assert "Locus" in guide[0].text
        for name in ("basic_graphing_assistant", "advanced_math_analysis", "visualize_3d"):
            prompt = await client.get_prompt(name, {"formula": "sin(x)"})
            assert prompt.messages


async def test_native_png_and_analysis(server):
    async with Client(server) as client:
        for name, args in [
            ("plot_math_function", {"formula": "3"}),
            ("plot_multiple_functions", {"formulas": ["sin(x)", "1/x", "sqrt(x)"], "y_range": [-4, 4]}),
        ]:
            result = await client.call_tool(name, args)
            image = next(block for block in result.content if block.type == "image")
            data = base64.b64decode(image.data)
            assert data.startswith(b"\x89PNG")
            assert Image.open(io.BytesIO(data)).size == (600, 400)
            metadata = json.loads(next(block.text for block in result.content if block.type == "text"))
            assert Path(metadata["path"]).read_bytes() == data
        result = await client.call_tool("analyze_formula", {"formula": "x^2", "analysis_type": "detailed"})
        assert result.data["stationary_points"] == "{0}"


async def test_invalid_calls_use_mcp_error(server):
    async with Client(server) as client:
        for args in ({"formula": "x", "x_range": [2, 1]}, {"formula": "2x"}):
            result = await client.call_tool("plot_math_function", args, raise_on_error=False)
            assert result.is_error
        result = await client.call_tool("plot_multiple_functions", {"formulas": []}, raise_on_error=False)
        assert result.is_error


async def test_surface_png(server):
    async with Client(server) as client:
        invalid = await client.call_tool("validate_formula", {"formula": "z = x^2 + y^2"})
        assert invalid.data["next_tool"] == "plot_3d_surface"
        result = await client.call_tool(
            "plot_3d_surface", {"formula": "z = x^2 + y^2", "x_range": [-2, 2], "y_range": [-2, 2], "z_range": [0, 8]}
        )
        image = next(block for block in result.content if block.type == "image")
        data = base64.b64decode(image.data)
        assert data.startswith(b"\x89PNG")
        assert Image.open(io.BytesIO(data)).size == (600, 400)
        metadata = json.loads(next(block.text for block in result.content if block.type == "text"))
        assert metadata["dimension"] == "3d"
        assert "x, y, z" in metadata["interaction"]
        assert Path(metadata["path"]).read_bytes() == data


async def test_explore_returns_one_picture(server):
    async with Client(server) as client:
        explored = await client.call_tool(
            "explore_functions",
            {"formulas": ["x^2", "2*x"], "x_range": [-2, 2], "y_range": [-1, 4], "analysis_type": "basic"},
        )
        metadata = json.loads(next(block.text for block in explored.content if block.type == "text"))
        assert [item["formula"] for item in metadata["analyses"]] == ["x^2", "2*x"]
        assert metadata["analyses"][0]["domain"] == "Reals"
        image = next(block for block in explored.content if block.type == "image")
        assert Image.open(io.BytesIO(base64.b64decode(image.data))).size == (600, 400)
        missing = await client.call_tool("plot_3d_surface", {}, raise_on_error=False)
        assert missing.is_error
        overlaid = await client.call_tool(
            "plot_math_function",
            {"formula": "x^2 if x < 0 else x", "x_range": [-2, 2], "show_derivative": True, "tangent_at": 1},
        )
        overlay_meta = json.loads(next(block.text for block in overlaid.content if block.type == "text"))
        assert overlay_meta["overlays"] == ["derivative", "tangent at 1"]
        points = await client.call_tool(
            "plot_points", {"points": [[0, 0], [1, 1], [2, 4]], "formula": "x^2", "x_range": [-1, 3]}
        )
        assert json.loads(next(block.text for block in points.content if block.type == "text"))["dimension"] == "2d"
        curve = await client.call_tool(
            "plot_parametric", {"x": "cos(t)", "y": "sin(t)", "z": "t", "t_range": [0, 3.141592653589793]}
        )
        assert json.loads(next(block.text for block in curve.content if block.type == "text"))["dimension"] == "3d"
        field = await client.call_tool(
            "plot_vector_field", {"fx": "-y", "fy": "x", "x_range": [-2, 2], "y_range": [-2, 2], "density": 8}
        )
        assert any(block.type == "image" for block in field.content)


async def test_timeout_terminates_worker():
    with pytest.raises(ToolError, match="exceeded"):
        await run_worker({"operation": "analyze", "formula": "x", "analysis_type": "basic"}, 0.001)


async def test_slow_worker_startup_does_not_consume_calculation_timeout(monkeypatch):
    class Input:
        def write(self, _data):
            pass

        async def drain(self):
            pass

        def close(self):
            pass

    class Output:
        async def readline(self):
            await asyncio.sleep(0.2)
            # Windows TextIO uses CRLF; the protocol must not compare raw lines.
            return b'{"ready": true}\r\n'

        async def read(self):
            return b'{"result": {"valid": true}}\n'

    class Error:
        async def read(self):
            return b""

    class Process:
        stdin, stdout, stderr = Input(), Output(), Error()
        returncode = 0

        async def wait(self):
            return 0

        async def communicate(self):
            return b"", b""

    async def create(*_args, **_kwargs):
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    result = await run_worker({"operation": "analyze"}, timeout=0.1)
    assert result == {"valid": True}


async def test_worker_startup_error_is_reported(monkeypatch):
    class Input:
        def write(self, _data):
            pass

        async def drain(self):
            pass

        def close(self):
            pass

    class Output:
        async def readline(self):
            return b'{"error": "font cache failed"}\n'

        async def read(self):
            return b""

    class Error:
        async def read(self):
            return b""

    class Process:
        stdin, stdout, stderr = Input(), Output(), Error()
        returncode = 1

        async def wait(self):
            return 1

        async def communicate(self):
            return b"", b""

    async def create(*_args, **_kwargs):
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    with pytest.raises(ToolError, match="font cache failed"):
        await run_worker({"operation": "render"}, timeout=1)


async def test_cancellation_reaps_worker(monkeypatch):
    original = asyncio.create_subprocess_exec
    started = asyncio.Event()
    processes = []

    async def capture(*args, **kwargs):
        process = await original(*args, **kwargs)
        processes.append(process)
        started.set()
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", capture)
    task = asyncio.create_task(run_worker({"operation": "analyze", "formula": "x", "analysis_type": "basic"}, 20))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert processes[0].returncode is not None


async def test_png_without_saving(tmp_path):
    server = create_server(Settings(output_dir=tmp_path, rendering=Rendering(save_files=False)))
    async with Client(server) as client:
        result = await client.call_tool("plot_math_function", {"formula": "x", "use_api": True})
        metadata = json.loads(next(block.text for block in result.content if block.type == "text"))
        assert "path" not in metadata
        assert "deprecated" in metadata["warnings"][0]
        assert any(block.type == "image" for block in result.content)
    assert list(tmp_path.iterdir()) == []


def test_config_relative_path_and_errors(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"output_dir": "artifacts"}))
    assert load_settings(str(path)).output_dir == tmp_path / "artifacts"
    path.write_text('{"rendering":{"default_width":1}}')
    with pytest.raises(ValueError):
        load_settings(str(path))


async def test_real_stdio_entrypoint(tmp_path):
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "locus.server"], cwd=tmp_path)
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            result = await client.call_tool("validate_formula", {"formula": "x^2"})
            assert result.structuredContent["valid"] is True
