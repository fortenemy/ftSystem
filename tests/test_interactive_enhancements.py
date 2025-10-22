from typer.testing import CliRunner

from main import app


def test_interactive_clear_and_last(tmp_path):
    runner = CliRunner()
    env = {"FTSYSTEM_SESSION_DIR": str(tmp_path / "sess")}
    # Use HelloAgent; call /clear, then provide a prompt to create a last reply, then /last, then /exit
    res = runner.invoke(
        app,
        [
            "interactive",
            "--agent",
            "HelloAgent",
        ],
        env=env,
        input="/clear\nHello\n/last\n/exit\n",
    )
    assert res.exit_code == 0, res.output
    assert "Screen cleared." in res.output
    assert "Hello, world!" in res.output  # last reply content appears

