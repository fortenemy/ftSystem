import json
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_session_tags_in_history(tmp_path: Path):
    runner = CliRunner()
    env = {"FTSYSTEM_HISTORY_DIR": str(tmp_path / "hist")}
    # Run with tag alpha
    res1 = runner.invoke(app, ["run", "--agent", "HelloAgent", "--tag", "alpha"], env=env)
    assert res1.exit_code == 0
    # Run with tag beta
    res2 = runner.invoke(app, ["run", "--agent", "HelloAgent", "--tag", "beta"], env=env)
    assert res2.exit_code == 0
    # Show only alpha
    res_show = runner.invoke(app, ["history", "show", "--json", "--tag", "alpha"], env=env)
    assert res_show.exit_code == 0
    arr = json.loads(res_show.output)
    assert isinstance(arr, list)
    assert all("alpha" in (itm.get("tags") or []) for itm in arr)

