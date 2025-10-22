import json
import sys
from pathlib import Path

from typer.testing import CliRunner

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from main import app  # noqa: E402


def test_perf_profile_json_output():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "perf",
            "profile",
            "--agent",
            "MasterAgent",
            "--rounds",
            "1",
            "--repeat",
            "2",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    text = result.stdout or result.output
    start = text.find("{")
    assert start != -1
    data = json.loads(text[start:])
    assert data["agent"] == "MasterAgent"
    assert data["runs"] == 2
    assert "durations" in data and len(data["durations"]) == 2
    assert data["rounds"] == 1
    assert "subagents" in data

