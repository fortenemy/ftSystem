from pathlib import Path
from typer.testing import CliRunner

from main import app


def test_rag_index_and_query(tmp_path: Path):
    # Prepare tiny corpus
    src = tmp_path / "kb"
    src.mkdir()
    (src / "one.txt").write_text("Python jest wspaniały. ftSystem używa Typer i Pydantic.", encoding="utf-8")
    (src / "two.md").write_text("## Nagłówek\n\nRAG demo: prosta wyszukiwarka tokenów i chunkowanie.", encoding="utf-8")

    runner = CliRunner()
    # Build index
    res = runner.invoke(app, ["rag", "index", "--src", str(src), "--index-dir", str(tmp_path / "index")])
    assert res.exit_code == 0, res.output
    assert "Index written:" in res.output

    # Query index
    res2 = runner.invoke(
        app,
        [
            "rag",
            "query",
            "--q",
            "ftSystem i Pydantic",
            "--index-dir",
            str(tmp_path / "index"),
            "--top-k",
            "3",
        ],
    )
    assert res2.exit_code == 0, res2.output
    # Should retrieve the file with ftSystem mention
    assert "one.txt#0" in res2.output

