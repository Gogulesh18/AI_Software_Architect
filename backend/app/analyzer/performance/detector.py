"""Performance findings: N+1 queries, blocking calls in async code, expensive
(nested) loops, repeated identical calls suggesting a missing cache.

Line-window heuristics rather than data-flow analysis: "does a query call
appear within N lines after a loop header" is cheap and catches the
overwhelmingly common real-world shape of these issues, at the cost of
missing indirection (a query hidden behind a helper function call).
"""

import re

from app.analyzer.models import Finding, findings_to_dicts
from app.parser.models import ParsedFile

_LOOP_HEADER_RE = re.compile(r"^\s*(for\b|while\b|\.forEach\(|\.map\(|\.each\b)")
_QUERY_CALL_RE = re.compile(
    r"(?i)\.(?:query|execute|filter|find|findOne|findAll|get|all|objects\.get|objects\.filter)\s*\(|"
    r"\bSELECT\s+.+\s+FROM\b"
)
_LOOP_WINDOW = 8

_ASYNC_HEADER_RE = re.compile(r"^\s*(?:export\s+)?async\s+(?:def|function)\b|:\s*async\s*\(|^\s*async\s*\(")
_BLOCKING_CALL_PATTERNS = [
    re.compile(r"\btime\.sleep\("),
    re.compile(r"\brequests\.(get|post|put|delete|patch)\("),
    re.compile(r"\bfs\.readFileSync\("),
    re.compile(r"\bfs\.writeFileSync\("),
    re.compile(r"\bexecSync\("),
]
_ASYNC_WINDOW = 15

_CACHE_HINT_RE = re.compile(r"(?i)\b(cache|memoiz|lru_cache)\b")


def analyze_performance(parsed_files: list[ParsedFile]) -> dict:
    findings: list[Finding] = []

    for pf in parsed_files:
        lines = pf.source.splitlines()
        findings.extend(_n_plus_one_findings(pf, lines))
        findings.extend(_blocking_call_findings(pf, lines))
        findings.extend(_repeated_call_findings(pf))

    for pf in parsed_files:
        for sym in pf.functions:
            if sym.max_loop_nesting >= 2:
                findings.append(
                    Finding(
                        "expensive_loop",
                        "medium",
                        pf.relative_path,
                        f"'{sym.name}' has {sym.max_loop_nesting} nested loops — likely O(n^{sym.max_loop_nesting}) or worse",
                        sym.start_line,
                        sym.name,
                    )
                )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: severity_order.get(f.severity, 5))

    by_category: dict[str, int] = {}
    for f in findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1

    return {"summary": by_category, "findings": findings_to_dicts(findings)}


def _n_plus_one_findings(pf: ParsedFile, lines: list[str]) -> list[Finding]:
    findings = []
    for i, line in enumerate(lines):
        if not _LOOP_HEADER_RE.match(line):
            continue
        window = lines[i + 1 : i + 1 + _LOOP_WINDOW]
        for offset, wline in enumerate(window):
            if _QUERY_CALL_RE.search(wline):
                findings.append(
                    Finding(
                        "n_plus_one_query",
                        "high",
                        pf.relative_path,
                        "query call inside a loop — likely N+1; consider batching/prefetching",
                        i + 1,
                    )
                )
                break
    return findings


def _blocking_call_findings(pf: ParsedFile, lines: list[str]) -> list[Finding]:
    findings = []
    for i, line in enumerate(lines):
        if not _ASYNC_HEADER_RE.search(line):
            continue
        window = lines[i + 1 : i + 1 + _ASYNC_WINDOW]
        for wline in window:
            for pattern in _BLOCKING_CALL_PATTERNS:
                m = pattern.search(wline)
                if m:
                    findings.append(
                        Finding(
                            "blocking_call",
                            "medium",
                            pf.relative_path,
                            f"blocking call '{m.group(0)}' inside an async function — use its async equivalent",
                            i + 1,
                        )
                    )
    return findings


def _repeated_call_findings(pf: ParsedFile) -> list[Finding]:
    findings = []
    for sym in pf.functions:
        if sym.kind not in ("function", "method") or not sym.calls:
            continue
        counts: dict[str, int] = {}
        for call in sym.calls:
            counts[call] = counts.get(call, 0) + 1
        repeated = {name: n for name, n in counts.items() if n >= 3}
        if not repeated:
            continue
        body_text = "\n".join(pf.source.splitlines()[sym.start_line - 1 : sym.end_line])
        if _CACHE_HINT_RE.search(body_text):
            continue  # already appears to cache/memoize
        for name, n in repeated.items():
            findings.append(
                Finding(
                    "missing_cache",
                    "low",
                    pf.relative_path,
                    f"'{name}' is called {n} times in '{sym.name}' with no visible caching/memoization",
                    sym.start_line,
                    sym.name,
                )
            )
    return findings
