import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_history_replay_pretty_prints(tmp_path):
    sess_dir = tmp_path / "sess"
    sess_dir.mkdir(parents=True, exist_ok=True)
    f = sess_dir / "session_HelloAgent_0000.jsonl"
    f.write_text(
        '\n'.join(
            [
                json.dumps({
                    "timestamp": "2025-09-10T10:00:00+00:00",
                    "role": "user",
                    "agent": "HelloAgent",
                    "text": "hi",
                }),
                json.dumps({
                    "timestamp": "2025-09-10T10:00:01+00:00",
                    "role": "agent",
                    "agent": "HelloAgent",
                    "text": "Hello, world!",
                }),
            ]
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    res = runner.invoke(app, ["history", "replay", str(f), "--limit", "2"]) 
    assert res.exit_code == 0, res.output
    out = res.output
    assert "[10:00:00] user: hi" in out
    assert "[10:00:01] agent(HelloAgent): Hello, world!" in out

