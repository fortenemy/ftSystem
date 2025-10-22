import os
from typer.testing import CliRunner

from main import app


def test_interactive_voice_mock(tmp_path):
    env = {**os.environ, "FTSYSTEM_SESSION_DIR": str(tmp_path / "sess"), "FTSYSTEM_MOCK_STT_TEXT": "Cześć ftSystem"}
    runner = CliRunner()
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
    assert "Transcribed:" in res.output
    assert "-> Hello, world!" in res.output

