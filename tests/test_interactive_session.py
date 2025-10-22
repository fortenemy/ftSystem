import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_interactive_persists_transcript(tmp_path):
    sess_dir = tmp_path / "sess"
    env = {**os.environ, "FTSYSTEM_SESSION_DIR": str(sess_dir)}
    runner = CliRunner()

    # Feed one input then exit
    res = runner.invoke(
        app,
        ["interactive", "--agent", "HelloAgent"],
        env=env,
        input="hello\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    # Expect a session file created
    files = list(sess_dir.glob("session_*_*.jsonl"))
    assert files, "no session transcript file created"
    content = files[0].read_text(encoding="utf-8").splitlines()
    assert len(content) >= 2
    first = json.loads(content[0])
    second = json.loads(content[1])
    assert first.get("role") == "user"
    assert second.get("role") == "agent"
    assert first.get("agent") == "HelloAgent"
    assert second.get("agent") == "HelloAgent"

