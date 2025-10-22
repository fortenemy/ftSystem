import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from agents import AGENT_REGISTRY
import json
from agents.base import AgentConfig


def test_master_agent_is_registered_and_runs():
    assert "MasterAgent" in AGENT_REGISTRY
    cls = AGENT_REGISTRY["MasterAgent"]
    agent = cls(AgentConfig(name="master", description="test"))
    res = agent.run()
    assert isinstance(res, dict)
    assert res.get("rounds") == 1
    results = res.get("results", {})
    # Expect HelloAgent output aggregated
    assert "HelloAgent" in results
    assert results["HelloAgent"] == "Hello, world!"


def test_master_agent_respects_subagents_yaml(tmp_path):
    # Create a YAML config that only requests HelloAgent
    cfg = tmp_path / "master.yaml"
    cfg.write_text(
        """
name: MasterAgent
description: test config
params:
  subagents:
    - HelloAgent
""".strip(),
        encoding="utf-8",
    )

    out = tmp_path / "out.json"
    from typer.testing import CliRunner
    from main import app

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
    assert isinstance(data, dict)
    assert data.get("rounds") == 1
    results = data.get("results", {})
    assert list(results.keys()) == ["HelloAgent"]


def test_master_agent_multiple_rounds(tmp_path):
    cfg = tmp_path / "master_rounds.yaml"
    cfg.write_text(
        """
name: MasterAgent
description: test rounds
params:
  subagents: [HelloAgent]
  rounds: 2
""".strip(),
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    from typer.testing import CliRunner
    from main import app

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
    assert data.get("rounds") == 2
    assert list(data.get("results", {}).keys()) == ["HelloAgent"]
