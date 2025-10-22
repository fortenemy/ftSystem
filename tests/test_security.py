import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_allowed_agents_filter(tmp_path, monkeypatch):
    # Allow only HelloAgent; config requests HelloAgent & SlowAgent
    monkeypatch.setenv("FTSYSTEM_ALLOWED_AGENTS", "HelloAgent")
    cfg = tmp_path / "master.yaml"
    cfg.write_text(
        """
name: MasterAgent
description: policy test
params:
  subagents: [HelloAgent, SlowAgent]
  rounds: 1
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
    import json

    data = json.loads(out.read_text(encoding="utf-8"))
    assert list(data.get("results", {}).keys()) == ["HelloAgent"]


def test_redactor_masks_user_input():
    from agents import AGENT_REGISTRY
    from agents.base import AgentConfig

    cls = AGENT_REGISTRY["MasterAgent"]
    agent = cls(AgentConfig(name="master", description="test"))
    res = agent.run(input="my key is sk-abc1234567890")
    transcript = res.get("transcript", [])
    # user message should be redacted
    user_msgs = [m for m in transcript if m.get("role") == "user"]
    assert user_msgs
    assert "sk-<redacted>" in user_msgs[0]["content"]


def test_redact_level_normal_does_not_mask_numbers():
    # default level is normal
    runner = CliRunner()
    env = {**os.environ, "FTSYSTEM_SESSION_DIR": "__tmp_sess__", "FTSYSTEM_MOCK_STT_TEXT": "email test@example.com cc 4111-1111-1111-1111"}
    res = runner.invoke(
        app,
        [
            "interactive",
            "--agent",
            "HelloAgent",
            "--voice-in",
            "mock",
            "--voice-out",
            "mock",
        ],
        env=env,
        input="/rec\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    # Email should be masked, numbers not in normal mode
    assert "<redacted-email>" in res.output
    assert "<redacted-number>" not in res.output


def test_redact_level_strict_masks_numbers():
    runner = CliRunner()
    env = {**os.environ, "FTSYSTEM_SESSION_DIR": "__tmp_sess__", "FTSYSTEM_MOCK_STT_TEXT": "email test@example.com cc 4111-1111-1111-1111 token Bearer abcdefghijkLMNOP1234"}
    res = runner.invoke(
        app,
        [
            "--redact-level",
            "strict",
            "interactive",
            "--agent",
            "HelloAgent",
            "--voice-in",
            "mock",
            "--voice-out",
            "mock",
        ],
        env=env,
        input="/rec\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    assert "<redacted-email>" in res.output
    assert "<redacted-number>" in res.output
    assert "Bearer <redacted-token>" in res.output
