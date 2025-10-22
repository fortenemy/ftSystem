import os
from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_security_redact_cli_levels(tmp_path: Path):
    runner = CliRunner()
    inp = tmp_path / "in.txt"
    out = tmp_path / "out.txt"
    text = (
        "email: test@example.com\n"
        "key: sk-abc1234567890\n"
        "token: Bearer abcdefghijkLMNOP1234\n"
        "cc: 4111-1111-1111-1111\n"
        "nip: 123-456-32-18\n"
        "vat: PL1234567890\n"
    )
    inp.write_text(text, encoding="utf-8")

    # Normal level via default
    res = runner.invoke(app, ["security", "redact", "--in", str(inp), "--out", str(out)])
    assert res.exit_code == 0, res.output
    out_text = out.read_text(encoding="utf-8")
    assert "<redacted-email>" in out_text
    assert "sk-<redacted>" in out_text
    assert "<redacted-number>" not in out_text
    assert "Bearer <redacted-token>" not in out_text
    assert "<redacted-nip>" not in out_text

    # Strict level
    out2 = tmp_path / "out2.txt"
    res2 = runner.invoke(app, ["security", "redact", "--in", str(inp), "--out", str(out2), "--level", "strict"])
    assert res2.exit_code == 0, res2.output
    out_text2 = out2.read_text(encoding="utf-8")
    assert "<redacted-number>" in out_text2
    assert "Bearer <redacted-token>" in out_text2
    assert "<redacted-nip>" in out_text2
