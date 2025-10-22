import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_history_find_across_days(tmp_path: Path):
    runner = CliRunner()
    env = {"FTSYSTEM_HISTORY_DIR": str(tmp_path / "hist")}
    # Create an older history file with a matching entry
    pdir = Path(env["FTSYSTEM_HISTORY_DIR"]) ; pdir.mkdir(parents=True, exist_ok=True)
    old_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    (pdir / f"history_{old_date}.jsonl").write_text(
        json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "agent": "HelloAgent", "status": "ok", "message": "needle here"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    # And generate today's entry using CLI run (data_preview will include HelloAgent output)
    res_run = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    assert res_run.exit_code == 0, res_run.output

    # Find across last 3 days
    res = runner.invoke(app, ["history", "find", "--contains", "needle", "--days", "3", "--json", "--limit", "1", "--reverse"], env=env)
    assert res.exit_code == 0, res.output
    data = json.loads(res.output)
    assert isinstance(data, dict)
    assert data.get("total", 0) >= 1
    assert any(obj.get("message") == "needle here" for obj in data.get("items", []))


def test_history_stats_json(tmp_path: Path):
    runner = CliRunner()
    env = {"FTSYSTEM_HISTORY_DIR": str(tmp_path / "hist2")}
    # Two entries for HelloAgent
    for _ in range(2):
        res = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
        assert res.exit_code == 0
    # One entry for ConfigEchoAgent
    res2 = runner.invoke(app, ["run", "--agent", "ConfigEchoAgent"], env=env)
    assert res2.exit_code == 0

    # Stats over last 1 day (today)
    res_stats = runner.invoke(app, ["history", "stats", "--days", "1", "--json"], env=env)
    assert res_stats.exit_code == 0, res_stats.output
    data = json.loads(res_stats.output)
    assert data["total"] >= 3
    assert data["by_agent"]["HelloAgent"] >= 2
    assert data["by_agent"]["ConfigEchoAgent"] >= 1
    # Agent-restricted stats
    res_stats_a = runner.invoke(app, ["history", "stats", "--days", "1", "--agent", "HelloAgent", "--json"], env=env)
    assert res_stats_a.exit_code == 0, res_stats_a.output
    data_a = json.loads(res_stats_a.output)
    assert data_a["total"] >= 2
    assert list(data_a["by_agent"].keys()) == ["HelloAgent"]
