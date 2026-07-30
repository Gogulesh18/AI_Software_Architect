"""Walk a materialized repo directory into a flat list of readable source files."""

import os
from dataclasses import dataclass
from pathlib import Path

from app.ingest.ignore_rules import is_ignored_dir, is_ignored_file


@dataclass(frozen=True, slots=True)
class FileRecord:
    relative_path: str  # POSIX-style, relative to repo root — used as the graph node id
    absolute_path: Path
    size_bytes: int


def enumerate_source_files(
    root: Path, max_files: int = 8000, max_file_size_bytes: int = 1_000_000
) -> list[FileRecord]:
    records: list[FileRecord] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_ignored_dir(d)]

        for filename in filenames:
            if is_ignored_file(filename):
                continue

            abs_path = Path(dirpath) / filename
            try:
                size = abs_path.stat().st_size
            except OSError:
                continue

            if size == 0 or size > max_file_size_bytes:
                continue
            if _looks_binary(abs_path):
                continue

            rel_path = abs_path.relative_to(root).as_posix()
            records.append(FileRecord(relative_path=rel_path, absolute_path=abs_path, size_bytes=size))

            if len(records) >= max_files:
                return records

    return records


def _looks_binary(path: Path, sniff_bytes: int = 2048) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(sniff_bytes)
    except OSError:
        return True
    return b"\x00" in chunk


def read_text_safe(path: Path) -> str | None:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            continue
    return None
