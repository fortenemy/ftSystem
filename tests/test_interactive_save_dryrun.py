import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_interactive_save_and_dryrun_tts(tmp_path: Path):
    runner = CliRunner()
    env = {
        **os.environ,
        "FTSYSTEM_SESSION_DIR": str(tmp_path / "sess"),
        "FTSYSTEM_MOCK_STT_TEXT": "whatever",
    }
    dest = tmp_path / "last.txt"
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
            "--dry-run-tts",
        ],
        env=env,
        input=f"/rec\n/save {dest}\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    # dry-run TTS should log instead of speaking
    assert "[TTS] Hello, world!" in res.output
    # save should write file
    assert dest.exists()
    assert "Hello, world!" in dest.read_text(encoding="utf-8")

