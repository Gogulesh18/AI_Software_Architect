"""Code quality: complexity, long methods, large/god classes, deep nesting,
magic numbers, duplicate code, and best-effort dead code detection.

Thresholds are conventional static-analysis defaults (McCabe >10 "high",
>50-line method "long", etc.), not tuned per-language — documented here so
they're easy to revisit. Dead-code detection is explicitly low-confidence:
it flags top-level functions with zero resolved callers in *this* graph,
which under-reports real usage whenever a caller lives in a file our
best-effort import/call resolver couldn't link (see app.graph.builder).
"""

import hashlib
import re
from collections import defaultdict

import networkx as nx

from app.analyzer.models import Finding, findings_to_dicts
from app.graph.builder import symbol_id
from app.parser.models import ParsedFile

LONG_METHOD_LOC = 50
LARGE_CLASS_LOC = 300
GOD_CLASS_METHOD_COUNT = 20
HIGH_COMPLEXITY = 10
VERY_HIGH_COMPLEXITY = 20
DEEP_NESTING = 4
DUPLICATE_BLOCK_LINES = 6
MAGIC_NUMBER_ALLOWLIST = {"0", "1", "-1", "2", "10", "60", "100", "200", "201", "204", "400", "401", "403", "404", "500", "1000", "3600"}

_TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|test_|_test\.|\.test\.|\.spec\.")
_CONST_DECL_RE = re.compile(r"^\s*(?:export\s+)?(?:const\s+)?[A-Z][A-Z0-9_]*\s*[:=]")
_NUMBER_RE = re.compile(r"(?<![\w.])(\d{2,}|\d+\.\d+)(?![\w])")


def analyze_quality(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph) -> dict:
    findings: list[Finding] = []

    complexities = []
    for pf in parsed_files:
        for sym in pf.symbols:
            if sym.kind in ("function", "method"):
                complexities.append(sym.complexity)
            findings.extend(_symbol_findings(pf, sym))

    findings.extend(_duplicate_code_findings(parsed_files))
    findings.extend(_dead_code_findings(parsed_files, graph))

    metrics = {
        "total_functions": len(complexities),
        "average_complexity": round(sum(complexities) / len(complexities), 2) if complexities else 0,
        "max_complexity": max(complexities, default=0),
        "high_complexity_functions": sum(1 for c in complexities if c > HIGH_COMPLEXITY),
    }

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: severity_order.get(f.severity, 5))

    return {"metrics": metrics, "findings": findings_to_dicts(findings)}


def _symbol_findings(pf: ParsedFile, sym) -> list[Finding]:
    findings: list[Finding] = []
    loc = sym.end_line - sym.start_line + 1

    if sym.kind in ("function", "method"):
        if sym.complexity > VERY_HIGH_COMPLEXITY:
            findings.append(Finding("high_complexity", "high", pf.relative_path, f"'{sym.name}' has cyclomatic complexity {sym.complexity} (very high, consider decomposing)", sym.start_line, sym.name))
        elif sym.complexity > HIGH_COMPLEXITY:
            findings.append(Finding("high_complexity", "medium", pf.relative_path, f"'{sym.name}' has cyclomatic complexity {sym.complexity}", sym.start_line, sym.name))

        if loc > LONG_METHOD_LOC:
            findings.append(Finding("long_method", "medium", pf.relative_path, f"'{sym.name}' is {loc} lines long (> {LONG_METHOD_LOC})", sym.start_line, sym.name))

        if sym.max_nesting_depth > DEEP_NESTING:
            findings.append(Finding("deep_nesting", "medium", pf.relative_path, f"'{sym.name}' nests {sym.max_nesting_depth} levels deep (> {DEEP_NESTING})", sym.start_line, sym.name))

    if sym.kind == "class":
        method_count = 0  # filled in by caller context via pf.functions below
        methods_in_class = [s for s in pf.functions if s.parent_class == sym.name]
        method_count = len(methods_in_class)

        if loc > LARGE_CLASS_LOC and method_count > GOD_CLASS_METHOD_COUNT:
            findings.append(Finding("god_class", "high", pf.relative_path, f"'{sym.name}' is a god class: {loc} lines, {method_count} methods", sym.start_line, sym.name))
        elif loc > LARGE_CLASS_LOC:
            findings.append(Finding("large_class", "medium", pf.relative_path, f"'{sym.name}' is {loc} lines long (> {LARGE_CLASS_LOC})", sym.start_line, sym.name))

    findings.extend(_magic_number_findings(pf, sym))
    return findings


def _magic_number_findings(pf: ParsedFile, sym) -> list[Finding]:
    findings: list[Finding] = []
    if sym.kind not in ("function", "method"):
        return findings

    lines = pf.source.splitlines()
    seen_this_symbol = 0
    for lineno in range(sym.start_line, min(sym.end_line, len(lines)) + 1):
        line = lines[lineno - 1]
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "*", "/*")) or _CONST_DECL_RE.match(line):
            continue
        for match in _NUMBER_RE.finditer(line):
            if match.group(1) in MAGIC_NUMBER_ALLOWLIST:
                continue
            findings.append(
                Finding("magic_number", "low", pf.relative_path, f"magic number {match.group(1)} in '{sym.name}'", lineno, sym.name)
            )
            seen_this_symbol += 1
            if seen_this_symbol >= 5:  # cap noise per-symbol
                return findings
    return findings


def _duplicate_code_findings(parsed_files: list[ParsedFile]) -> list[Finding]:
    blocks: dict[str, list[tuple[str, int]]] = defaultdict(list)

    for pf in parsed_files:
        lines = [ln.strip() for ln in pf.source.splitlines()]
        non_test = not _TEST_PATH_RE.search(pf.relative_path)
        if not non_test:
            continue
        for i in range(max(0, len(lines) - DUPLICATE_BLOCK_LINES + 1)):
            window = lines[i : i + DUPLICATE_BLOCK_LINES]
            if sum(1 for ln in window if ln) < DUPLICATE_BLOCK_LINES - 1:
                continue  # too many blank lines to be meaningful
            normalized = "\n".join(window)
            if len(normalized) < 40:
                continue  # trivial short blocks (closing braces etc.) aren't meaningful dupes
            digest = hashlib.sha1(normalized.encode("utf-8", errors="replace")).hexdigest()
            blocks[digest].append((pf.relative_path, i + 1))

    findings: list[Finding] = []
    reported_files: set[tuple[str, str]] = set()
    for digest, occurrences in blocks.items():
        if len(occurrences) < 2:
            continue
        locations = sorted(set(occurrences))
        if len(locations) < 2:
            continue
        first_file, first_line = locations[0]
        key = (first_file, digest)
        if key in reported_files:
            continue
        reported_files.add(key)
        other_locations = ", ".join(f"{f}:{ln}" for f, ln in locations[1:3])
        findings.append(
            Finding(
                "duplicate_code",
                "low",
                first_file,
                f"{DUPLICATE_BLOCK_LINES}-line block duplicated at {other_locations}"
                + (f" and {len(locations) - 3} more" if len(locations) > 3 else ""),
                first_line,
                None,
            )
        )
        if len(findings) >= 50:  # cap total duplicate findings to keep the report readable
            break
    return findings


def _dead_code_findings(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph) -> list[Finding]:
    findings: list[Finding] = []
    _COMMON_ENTRYPOINTS = {"main", "__init__", "__new__", "setup", "handler", "run"}

    for pf in parsed_files:
        if _TEST_PATH_RE.search(pf.relative_path):
            continue
        for func in pf.functions:
            if func.kind != "function":  # methods excluded: too many false positives (interfaces, overrides)
                continue
            if func.decorators or func.name in _COMMON_ENTRYPOINTS or func.name.startswith("test_"):
                continue
            node_id = symbol_id(pf.relative_path, func.name)
            if not graph.has_node(node_id):
                continue
            has_caller = any(data.get("type") == "calls" for _, _, data in graph.in_edges(node_id, data=True))
            if not has_caller:
                findings.append(
                    Finding(
                        "dead_code",
                        "low",
                        pf.relative_path,
                        f"'{func.name}' has no resolved callers in this repo (may be dynamic, tests-only, or public API)",
                        func.start_line,
                        func.name,
                    )
                )
    return findings
