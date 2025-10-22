import json
import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def _env(tmp_path: Path) -> dict:
    return {**os.environ, "FTSYSTEM_HISTORY_DIR": str(tmp_path / "hist")}


def test_history_export_and_clear(tmp_path: Path):
    runner = CliRunner()
    env = _env(tmp_path)
    # generate a couple of history entries
    for _ in range(2):
        res_run = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
        assert res_run.exit_code == 0, res_run.output

    # export
    out = tmp_path / "out.jsonl"
    res_exp = runner.invoke(app, ["history", "export", "--out", str(out)], env=env)
    assert res_exp.exit_code == 0, res_exp.output
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
    # jsonl validity
    for ln in lines:
        json.loads(ln)

    # clear
    res_clear = runner.invoke(app, ["history", "clear", "--yes"], env=env)
    assert res_clear.exit_code == 0, res_clear.output
    # file should be gone in configured history dir
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hp = Path(env["FTSYSTEM_HISTORY_DIR"]) / f"history_{today}.jsonl"
    assert not hp.exists()


def test_history_export_with_tag(tmp_path: Path):
    runner = CliRunner()
    env = _env(tmp_path)
    # one entry without tag
    res0 = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    assert res0.exit_code == 0
    # one entry with tag=alpha
    res1 = runner.invoke(app, ["run", "--agent", "HelloAgent", "--tag", "alpha"], env=env)
    assert res1.exit_code == 0
    # export only tag alpha
    out = tmp_path / "out_tag.jsonl"
    res_exp = runner.invoke(app, ["history", "export", "--out", str(out), "--tag", "alpha"], env=env)
    assert res_exp.exit_code == 0, res_exp.output
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    import json as _json

    for ln in lines:
        obj = _json.loads(ln)
        assert "alpha" in (obj.get("tags") or [])


def test_history_show_json(tmp_path: Path):
    runner = CliRunner()
    env = _env(tmp_path)
    res_run = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    assert res_run.exit_code == 0, res_run.output
    res_show = runner.invoke(app, ["history", "show", "--json", "--limit", "1"], env=env)
    assert res_show.exit_code == 0, res_show.output
    arr = json.loads(res_show.output.strip()) if res_show.output.strip().startswith("[") else []
    assert isinstance(arr, list)
    assert len(arr) <= 1


def test_history_prune_keep(tmp_path: Path):
    runner = CliRunner()
    env = _env(tmp_path)
    # create a few entries
    for _ in range(3):
        res = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
        assert res.exit_code == 0
    # prune to last 1
    res2 = runner.invoke(app, ["history", "prune", "--keep", "1", "--yes"], env=env)
    assert res2.exit_code == 0, res2.output
    # verify
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    hp = Path(env["FTSYSTEM_HISTORY_DIR"]) / f"history_{today}.jsonl"
    lines = hp.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_history_prune_days(tmp_path: Path):
    runner = CliRunner()
    env = _env(tmp_path)
    # Build two history files: one old, one today
    from datetime import datetime, timedelta, timezone

    pdir = Path(env["FTSYSTEM_HISTORY_DIR"]) or tmp_path / "hist"
    pdir.mkdir(parents=True, exist_ok=True)
    old_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
    (pdir / f"history_{old_date}.jsonl").write_text("{}\n", encoding="utf-8")
    # generate today's file by running once
    _ = runner.invoke(app, ["run", "--agent", "HelloAgent"], env=env)
    # prune files older than 1 day
    res = runner.invoke(app, ["history", "prune", "--days", "1", "--yes"], env=env)
    assert res.exit_code == 0, res.output
    # old should be gone
    assert not (pdir / f"history_{old_date}.jsonl").exists()
