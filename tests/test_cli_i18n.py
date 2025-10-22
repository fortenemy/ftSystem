import sys
from pathlib import Path

from typer.testing import CliRunner

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from main import app  # noqa: E402


def test_run_command_in_polish_language():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--lang",
            "pl",
            "run",
            "--agent",
            "NieMa",
        ],
    )
    assert result.exit_code != 0
    assert "nie został znaleziony" in result.output

