import json
from typer.testing import CliRunner

from main import app


def test_voice_profile_set_show(tmp_path):
    runner = CliRunner()
    env = {"FTSYSTEM_CONFIG_DIR": str(tmp_path / "cfg")}
    # Show default (empty)
    res_show0 = runner.invoke(app, ["voice", "profile", "--show"], env=env)
    assert res_show0.exit_code == 0
    data0 = json.loads(res_show0.output)
    # Set values
    res_set = runner.invoke(
        app,
        [
            "voice",
            "profile",
            "--set",
            "--voice-lang",
            "en-US",
            "--mic-index",
            "2",
            "--no-beep",
        ],
        env=env,
    )
    assert res_set.exit_code == 0
    # Show again
    res_show = runner.invoke(app, ["voice", "profile", "--show"], env=env)
    assert res_show.exit_code == 0
    data = json.loads(res_show.output)
    assert data.get("voice_lang") == "en-US"
    assert data.get("mic_index") == 2
    assert data.get("beep") is False

