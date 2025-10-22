import sys
from pathlib import Path

from typer.testing import CliRunner

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from main import app  # noqa: E402


def test_metrics_export_from_run(tmp_path):
    metrics_file = tmp_path / "metrics.prom"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "--agent",
            "MasterAgent",
            "--metrics-path",
            str(metrics_file),
        ],
    )
    assert result.exit_code == 0, result.output
    text = metrics_file.read_text(encoding="utf-8")
    assert "ftsystem_run_duration_seconds" in text
    assert 'ftsystem_subagent_latency_seconds{agent="MasterAgent"' in text

