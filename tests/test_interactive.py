import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_interactive_loop_persists_history(tmp_path):
    hist_dir = tmp_path / "hist"
    env = {**os.environ, "FTSYSTEM_HISTORY_DIR": str(hist_dir)}
    runner = CliRunner()

    # Feed one input then exit
    res = runner.invoke(
        app,
        ["interactive", "--agent", "HelloAgent"],
        env=env,
        input="hello\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    # Should print agent output
    assert "Hello, world!" in res.output
    # History contains timestamp with timezone and agent
    files = list(hist_dir.glob("history_*.jsonl"))
    assert files, "history file not created"
    content = files[0].read_text(encoding="utf-8").splitlines()
    assert content, "history is empty"
    obj = json.loads(content[-1])
    assert obj.get("agent") == "HelloAgent"
    ts = obj.get("timestamp", "")
    assert "+00:00" in ts or ts.endswith("Z")

