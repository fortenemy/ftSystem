import json
from typer.testing import CliRunner

from main import app


def test_list_agents_json():
    runner = CliRunner()
    res = runner.invoke(app, ["list-agents", "--format", "json", "--verbose"])
    assert res.exit_code == 0, res.output
    data = json.loads(res.output)
    assert "agents" in data
    names = [a["name"] for a in data["agents"]]
    assert "HelloAgent" in names

