import json
from pathlib import Path
from typer.testing import CliRunner

from main import app, complete_agent


def test_cli_run_with_yaml_config(tmp_path):
    cfg = tmp_path / "hello.yaml"
    cfg.write_text(
        """
name: hello
description: YAML config for HelloAgent
""".strip(),
        encoding="utf-8",
    )
    out_file = tmp_path / "result.json"
    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "run",
            "--agent",
            "HelloAgent",
            "--config",
            str(cfg),
            "--output",
            str(out_file),
        ],
    )
    assert res.exit_code == 0, res.output
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data == "Hello, world!"


def test_agent_autocompletion_function():
    # Should suggest HelloAgent for prefix "he" (case-insensitive)
    suggestions = complete_agent("he")
    assert any(s == "HelloAgent" for s in suggestions)
