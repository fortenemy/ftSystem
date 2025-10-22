from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


_TOKEN_RE = re.compile(r"[a-zA-ZąćęłńóśżźĄĆĘŁŃÓŚŻŹ0-9_]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _chunk_paragraphs(text: str, target_size: int = 600, overlap: int = 100) -> List[str]:
    # Split by blank lines, then pack paragraphs to target size with overlap windows
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        return []
    chunks: List[str] = []
    buf: List[str] = []
    cur = 0
    for p in paras:
        if cur + len(p) + 1 <= target_size or not buf:
            buf.append(p)
            cur += len(p) + 1
        else:
            chunks.append("\n\n".join(buf))
            # start new buffer with overlap from end
            joined = "\n\n".join(buf)
            if len(joined) > overlap:
                # keep last overlap characters
                tail = joined[-overlap:]
                buf = [tail, p]
                cur = len(tail) + len(p) + 1
            else:
                buf = [p]
                cur = len(p) + 1
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


@dataclass
class Chunk:
    id: str
    doc_path: str
    chunk_idx: int
    text: str
    tokens: List[str]


def build_index(src: Path, index_dir: Path) -> Path:
    index_dir.mkdir(parents=True, exist_ok=True)
    out = index_dir / "chunks.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for path in _iter_files(src, {".txt", ".md"}):
            rel = str(path)
            text = _read_text_file(path)
            for i, ch in enumerate(_chunk_paragraphs(text)):
                cid = f"{path.name}:{i}"
                rec = {
                    "id": cid,
                    "doc_path": rel,
                    "chunk_idx": i,
                    "text": ch,
                    "tokens": _tokenize(ch),
                }
                f.write(json.dumps(rec, ensure_ascii=False))
                f.write("\n")
    return out


def _iter_files(root: Path, exts: Iterable[str]) -> Iterable[Path]:
    exts_lower = {e.lower() for e in exts}
    if root.is_file():
        if root.suffix.lower() in exts_lower:
            yield root
        return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts_lower:
            yield p


def _score(tokens_q: List[str], tokens_doc: List[str]) -> float:
    if not tokens_q or not tokens_doc:
        return 0.0
    set_q = set(tokens_q)
    set_d = set(tokens_doc)
    # Simple Jaccard-like score with frequency hint
    inter = set_q.intersection(set_d)
    return len(inter) + 0.1 * min(len(tokens_doc), 100) / 100.0


def query_index(index_dir: Path, query: str, top_k: int = 5) -> List[Tuple[float, dict]]:
    idx = index_dir / "chunks.jsonl"
    if not idx.exists():
        raise FileNotFoundError(f"Index not found: {idx}")
    q_tokens = _tokenize(query)
    scored: List[Tuple[float, dict]] = []
    with idx.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            s = _score(q_tokens, rec.get("tokens") or [])
            if s > 0:
                scored.append((s, rec))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[: max(1, int(top_k))]

