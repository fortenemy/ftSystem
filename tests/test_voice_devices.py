from typer.testing import CliRunner

from main import app


def test_voice_devices_cmd_runs():
    runner = CliRunner()
    res = runner.invoke(app, ["voice", "devices"])
    assert res.exit_code == 0, res.output
    # Either lists devices or prints a note about missing deps
    assert ("Microphones:" in res.output) or ("not installed" in res.output)

