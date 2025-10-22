import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_history_persist_and_show(tmp_path):
    # Redirect history dir
    hist_dir = tmp_path / "hist"
    env = {**os.environ, "FTSYSTEM_HISTORY_DIR": str(hist_dir)}
    runner = CliRunner()

    # Run an agent to produce a summary entry
    res_run = runner.invoke(
        app,
        ["run", "--agent", "HelloAgent"],
        env=env,
    )
    assert res_run.exit_code == 0, res_run.output

    # Show history
    res_hist = runner.invoke(app, ["history", "show", "--limit", "5"], env=env)
    assert res_hist.exit_code == 0, res_hist.output
    # Should include a JSON line with agent HelloAgent
    found = False
    for line in res_hist.output.splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("agent") == "HelloAgent":
            found = True
            break
    assert found, res_hist.output

