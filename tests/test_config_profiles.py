import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_layered_config_env_cli_file(tmp_path):
    cfg = tmp_path / "agent.yaml"
    cfg.write_text(
        """
name: from_file
description: from_file
params:
  a: 1
  b: 2
""".strip(),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    env = {
        **os.environ,
        "FTSYSTEM_AGENT_NAME": "from_env",
        "FTSYSTEM_AGENT_DESCRIPTION": "from_env_desc",
        "FTSYSTEM_PARAMS": json.dumps({"a": 9, "c": 3}),
    }
    runner = CliRunner()
    res = runner.invoke(
        app,
        [
            "run",
            "--agent",
            "ConfigEchoAgent",
            "--config",
            str(cfg),
            "--param",
            "b=10",
            "--param",
            "d=\"ok\"",
            "--output",
            str(out),
        ],
        env=env,
    )
    assert res.exit_code == 0, res.output
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["name"] == "from_env"
    assert data["description"] == "from_env_desc"
    # params merged: file a=1,b=2 + env a=9,c=3 + cli b=10,d="ok" => a=9,b=10,c=3,d=ok
    assert data["params"]["a"] == 9
    assert data["params"]["b"] == 10
    assert data["params"]["c"] == 3
    assert data["params"]["d"] == "ok"

