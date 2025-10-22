import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_history_filters_by_agent_and_contains(tmp_path):
    hist_dir = tmp_path / "hist"
    env = {**os.environ, "FTSYSTEM_HISTORY_DIR": str(hist_dir)}
    runner = CliRunner()

    # Produce two entries
    res1 = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    assert res1.exit_code == 0, res1.output
    res2 = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    assert res2.exit_code == 0, res2.output

    # Should filter by agent and contains
    res_show = runner.invoke(
        app,
        ["history", "show", "--limit", "5", "--agent", "HelloAgent", "--contains", "Hello"],
        env=env,
    )
    assert res_show.exit_code == 0, res_show.output
    # All lines should be JSON and match agent
    lines = [l for l in res_show.output.splitlines() if l.strip()]
    assert lines, res_show.output
    for line in lines:
        obj = json.loads(line)
        assert obj.get("agent") == "HelloAgent"
        assert "Hello" in (obj.get("message") or "") or "Hello" in (obj.get("data_preview") or "")

