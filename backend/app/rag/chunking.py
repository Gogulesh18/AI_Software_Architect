"""Splits parsed files into retrieval chunks: one chunk per function/class
for deep-parsed languages (a symbol is a natural, self-contained unit of
meaning), a sliding line-window for everything else (markdown, config,
shallow-parsed languages)."""

from dataclasses import dataclass

from app.parser.models import ParsedFile

MAX_CHARS = 2500
WINDOW_LINES = 60
OVERLAP_LINES = 10


@dataclass(slots=True)
class Chunk:
    text: str
    file: str
    start_line: int
    end_line: int
    symbol: str | None = None


def chunk_file(pf: ParsedFile) -> list[Chunk]:
    if pf.symbols:
        return _symbol_chunks(pf)
    return _window_chunks(pf)


def _symbol_chunks(pf: ParsedFile) -> list[Chunk]:
    lines = pf.source.splitlines()
    chunks = []
    for sym in pf.symbols:
        text = "\n".join(lines[sym.start_line - 1 : sym.end_line])
        if not text.strip():
            continue
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n... (truncated)"
        chunks.append(Chunk(text=text, file=pf.relative_path, start_line=sym.start_line, end_line=sym.end_line, symbol=sym.name))
    return chunks


def _window_chunks(pf: ParsedFile) -> list[Chunk]:
    lines = pf.source.splitlines()
    if not lines:
        return []
    chunks = []
    step = WINDOW_LINES - OVERLAP_LINES
    for start in range(0, len(lines), step):
        window = lines[start : start + WINDOW_LINES]
        text = "\n".join(window)
        if not text.strip():
            continue
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n... (truncated)"
        chunks.append(Chunk(text=text, file=pf.relative_path, start_line=start + 1, end_line=min(start + WINDOW_LINES, len(lines))))
        if start + WINDOW_LINES >= len(lines):
            break
    return chunks


def chunk_repository(parsed_files: list[ParsedFile]) -> list[Chunk]:
    chunks = []
    for pf in parsed_files:
        chunks.extend(chunk_file(pf))
    return chunks
