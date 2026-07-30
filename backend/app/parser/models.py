"""Data model produced by parsing a single source file."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedSymbol:
    kind: str  # "class" | "function" | "method"
    name: str
    start_line: int
    end_line: int
    decorators: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)  # unresolved callee names, best-effort
    complexity: int = 1  # McCabe-style approximation, base 1
    max_nesting_depth: int = 0
    max_loop_nesting: int = 0  # nested-loop depth only (if/else don't count) — used for perf "expensive loop" checks
    parent_class: str | None = None
    base_classes: list[str] = field(default_factory=list)  # classes only; extends/implements targets


@dataclass(slots=True)
class ParsedFile:
    relative_path: str
    language: str
    loc: int
    imports: list[str] = field(default_factory=list)
    symbols: list[ParsedSymbol] = field(default_factory=list)
    parse_error: str | None = None
    # Kept for analyzers that need line-level text (security/perf/magic-number
    # regex scans) rather than just AST structure. Repos are already capped by
    # max_files_per_repo/max_file_size_bytes, so holding this in memory for the
    # duration of one analysis job is an acceptable trade-off.
    source: str = ""

    def line(self, lineno: int) -> str:
        lines = self.source.splitlines()
        return lines[lineno - 1] if 0 < lineno <= len(lines) else ""

    @property
    def classes(self) -> list[ParsedSymbol]:
        return [s for s in self.symbols if s.kind == "class"]

    @property
    def functions(self) -> list[ParsedSymbol]:
        return [s for s in self.symbols if s.kind in ("function", "method")]
