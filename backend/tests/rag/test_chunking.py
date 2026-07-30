from app.parser.extractor import parse_source
from app.rag.chunking import chunk_file, chunk_repository


def test_symbol_chunking_produces_one_chunk_per_symbol():
    src = "class Foo:\n    def bar(self):\n        pass\n\n\ndef baz():\n    pass\n"
    pf = parse_source("a.py", "python", src)
    chunks = chunk_file(pf)

    symbols = {c.symbol for c in chunks}
    assert symbols == {"Foo", "bar", "baz"}
    for c in chunks:
        assert c.file == "a.py"
        assert c.text.strip()


def test_window_chunking_for_files_without_symbols():
    lines = "\n".join(f"line {i}" for i in range(150))
    pf = parse_source("README.md", "markdown", lines)
    chunks = chunk_file(pf)

    assert len(chunks) > 1
    assert all(c.symbol is None for c in chunks)
    assert chunks[0].start_line == 1


def test_empty_file_produces_no_chunks():
    pf = parse_source("empty.py", "python", "")
    assert chunk_file(pf) == []


def test_chunk_repository_aggregates_all_files():
    files = [
        parse_source("a.py", "python", "def f():\n    pass\n"),
        parse_source("b.py", "python", "def g():\n    pass\n"),
    ]
    chunks = chunk_repository(files)
    assert {c.file for c in chunks} == {"a.py", "b.py"}


def test_long_symbol_is_truncated():
    body = "\n".join(f"    x{i} = {i}" for i in range(2000))
    src = f"def big():\n{body}\n"
    pf = parse_source("a.py", "python", src)
    chunks = chunk_file(pf)
    assert len(chunks[0].text) <= 2600
    assert chunks[0].text.endswith("(truncated)")
