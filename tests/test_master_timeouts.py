import json
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_master_agent_timeout_marks_result(tmp_path):
    cfg = tmp_path / "master_timeout.yaml"
    cfg.write_text(
        """
name: MasterAgent
description: timeout test
params:
  subagents: [SlowAgent]
  rounds: 1
  timeout_seconds: 0.05
""".strip(),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "run",
            "--agent",
            "MasterAgent",
            "--config",
            str(cfg),
            "--output",
            str(out),
        ],
    )
    assert res.exit_code == 0, res.output
    data = json.loads(out.read_text(encoding="utf-8"))
    results = data.get("results", {})
    assert "SlowAgent" in results
    assert isinstance(results["SlowAgent"], dict) and results["SlowAgent"].get("error") == "timeout"

