import sys
from pathlib import Path
from pypdf import PdfReader


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python scripts/extract_pdf_text.py <input.pdf> <output.txt>")
        return 1
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    reader = PdfReader(str(in_path))
    lines = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = f"<Error extracting page {i}: {e}>\n"
        lines.append(f"\n=== Page {i} ===\n")
        lines.append(text)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote text to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

