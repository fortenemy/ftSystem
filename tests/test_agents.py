
import sys
from pathlib import Path

# Ensure src/ is in sys.path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
import logging
from typer.testing import CliRunner
from main import app
from agents import AGENT_REGISTRY
from agents.base import AgentConfig

def test_agent_registry_listing():
    """Test that at least one agent is registered."""
    assert len(AGENT_REGISTRY) > 0
    assert "HelloAgent" in AGENT_REGISTRY

def test_hello_agent_run(caplog):
    """Test that HelloAgent.run() returns and logs the expected output."""
    agent_cls = AGENT_REGISTRY["HelloAgent"]
    config = AgentConfig(name="hello", description="pytest config")
    agent = agent_cls(config)
    with caplog.at_level(logging.INFO):
        result = agent.run()
    assert result == "Hello, world!"
    assert any("Hello, world!" in r.message for r in caplog.records)


def test_cli_run_with_output(tmp_path):
    """Test CLI 'run' command with --output saving JSON result."""
    runner = CliRunner()
    out_file = tmp_path / "result.json"
    res = runner.invoke(
        app,
        [
            "run",
            "--agent",
            "HelloAgent",
            "--config",
            str(Path("hello_config.json")),
            "--output",
            str(out_file),
        ],
    )
    assert res.exit_code == 0, res.output
    assert out_file.exists()
    import json

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == "Hello, world!"


def test_cli_log_level_controls_debug_output():
    """Debug log appears only when --log-level=DEBUG is set."""
    runner = CliRunner()
    # By default (INFO) debug init message should not appear
    res_info = runner.invoke(app, ["list-agents"]) 
    assert res_info.exit_code == 0, res_info.output
    assert "ftsystem logger initialized" not in res_info.output

    # With DEBUG it should appear
    res_debug = runner.invoke(app, ["--log-level", "DEBUG", "list-agents"]) 
    assert res_debug.exit_code == 0, res_debug.output
    assert "ftsystem logger initialized" in res_debug.output


def test_cli_list_agents_verbose_includes_details():
    runner = CliRunner()
    res = runner.invoke(app, ["list-agents", "--verbose"]) 
    assert res.exit_code == 0, res.output
    # Should include HelloAgent and its module path
    assert "HelloAgent (agents.hello_agent)" in res.output
    # And show a doc line
    assert "doc:" in res.output


def test_cli_new_agent_generates_files(tmp_path):
    runner = CliRunner()
    target = tmp_path / "agents"
    cfg = tmp_path / "cfg.json"
    res = runner.invoke(
        app,
        [
            "new-agent",
            "Sample",
            "--target-dir",
            str(target),
            "--config-out",
            str(cfg),
        ],
    )
    assert res.exit_code == 0, res.output
    # File and config are created
    agent_file = target / "sample_agent.py"
    assert agent_file.exists(), res.output
    assert cfg.exists(), res.output
    text = agent_file.read_text(encoding="utf-8")
    assert "class SampleAgent(Agent):" in text
