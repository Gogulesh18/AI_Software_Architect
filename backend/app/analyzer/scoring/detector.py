"""Aggregate every analyzer's findings into the 9 brief-mandated engineering
scores (0-100), each with the reasoning behind the number.

Scores are penalty-based (start at 100, subtract weighted findings) rather
than ML-derived — deterministic, reproducible, and each point loss traces
back to a specific finding count, which is what "must include reasoning"
in the brief actually requires.
"""

import re

from app.graph.summary import RepoSummary
from app.parser.models import ParsedFile

_TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|test_|_test\.|\.test\.|\.spec\.")
_COMMENT_PREFIXES = ("#", "//", "*", "/*", '"""', "'''")

_SEVERITY_PENALTY = {"critical": 25, "high": 14, "medium": 7, "low": 3, "info": 1}


def _clamp(score: float) -> int:
    return max(0, min(100, round(score)))


def _penalize(findings: list[dict], per_severity: dict[str, int] | None = None) -> tuple[int, list[str]]:
    weights = per_severity or _SEVERITY_PENALTY
    score = 100.0
    counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "low")
        counts[sev] = counts.get(sev, 0) + 1
        score -= weights.get(sev, 3)
    reasoning = [f"{n} {sev} finding(s)" for sev, n in sorted(counts.items(), key=lambda kv: _SEVERITY_PENALTY.get(kv[0], 3), reverse=True)]
    if not reasoning:
        reasoning = ["no findings in this category"]
    return _clamp(score), reasoning


def compute_scores(
    parsed_files: list[ParsedFile],
    summary: RepoSummary,
    architecture: dict,
    quality: dict,
    security: dict,
    performance: dict,
    solid: dict,
) -> dict:
    scores: dict[str, dict] = {}

    scores["architecture"] = {
        "score": architecture["confidence"],
        "reasoning": architecture["evidence"] or [f"classified as {architecture['primary_style']} by default"],
    }

    sec_score, sec_reason = _penalize(security["findings"])
    scores["security"] = {"score": sec_score, "reasoning": sec_reason}

    perf_score, perf_reason = _penalize(performance["findings"], {"high": 12, "medium": 6, "low": 2})
    scores["performance"] = {"score": perf_score, "reasoning": perf_reason}

    maintain_score, maintain_reason = _maintainability(quality, solid)
    scores["maintainability"] = {"score": maintain_score, "reasoning": maintain_reason}

    scores["readability"] = _readability(quality)

    scores["scalability"] = _scalability(architecture, performance)

    scores["testability"] = _testability(parsed_files, summary, solid)

    scores["documentation"] = _documentation(parsed_files, summary)

    weights = {
        "architecture": 0.15,
        "security": 0.20,
        "performance": 0.15,
        "maintainability": 0.20,
        "readability": 0.10,
        "scalability": 0.10,
        "testability": 0.05,
        "documentation": 0.05,
    }
    overall = sum(scores[k]["score"] * w for k, w in weights.items())
    scores["overall"] = {
        "score": _clamp(overall),
        "reasoning": [f"weighted average of the 8 category scores (weights: {weights})"],
    }

    return scores


def _maintainability(quality: dict, solid: dict) -> tuple[int, list[str]]:
    weights = {"critical": 20, "high": 10, "medium": 5, "low": 2, "info": 1}
    score, reasoning = _penalize(quality["findings"], weights)
    solid_penalty = len(solid["violations"]) * 3
    score = _clamp(score - solid_penalty)
    if solid["violations"]:
        reasoning.append(f"{len(solid['violations'])} SOLID violation(s)")
    return score, reasoning


def _readability(quality: dict) -> dict:
    relevant = [f for f in quality["findings"] if f["category"] in ("magic_number", "deep_nesting", "long_method")]
    score, reasoning = _penalize(relevant, {"critical": 15, "high": 8, "medium": 5, "low": 2, "info": 1})
    avg_complexity = quality["metrics"]["average_complexity"]
    if avg_complexity > 8:
        score = _clamp(score - 10)
        reasoning.append(f"average cyclomatic complexity {avg_complexity} is high")
    return {"score": score, "reasoning": reasoning}


_SCALABLE_STYLES = {"Microservices", "Event-Driven", "Serverless"}


def _scalability(architecture: dict, performance: dict) -> dict:
    score = 70 if architecture["primary_style"] in _SCALABLE_STYLES else 55
    reasoning = [f"baseline for {architecture['primary_style']} architecture"]

    perf_categories = {f["category"] for f in performance["findings"]}
    if "n_plus_one_query" in perf_categories:
        score -= 15
        reasoning.append("N+1 query patterns limit horizontal scalability")
    if "expensive_loop" in perf_categories:
        score -= 10
        reasoning.append("nested loops found — may not scale with input size")
    if "blocking_call" in perf_categories:
        score -= 10
        reasoning.append("blocking calls found in async code paths")
    if not perf_categories:
        reasoning.append("no scalability-limiting performance findings")

    return {"score": _clamp(score), "reasoning": reasoning}


def _testability(parsed_files: list[ParsedFile], summary: RepoSummary, solid: dict) -> dict:
    test_files = sum(1 for pf in parsed_files if _TEST_PATH_RE.search(pf.relative_path))
    code_files = sum(1 for pf in parsed_files if pf.language not in ("json", "yaml", "markdown", "toml", "xml", "text", "other"))
    ratio = test_files / code_files if code_files else 0

    score = _clamp(ratio * 200)  # 50% test-file ratio -> 100
    reasoning = [f"{test_files} test file(s) out of {code_files} code file(s) ({ratio:.0%} ratio)"]

    dip_violations = sum(1 for v in solid["violations"] if v["principle"] == "DIP")
    if dip_violations:
        score = _clamp(score - dip_violations * 4)
        reasoning.append(f"{dip_violations} DIP violation(s) (direct construction of dependencies) make unit testing harder")

    return {"score": score, "reasoning": reasoning}


def _documentation(parsed_files: list[ParsedFile], summary: RepoSummary) -> dict:
    has_readme = any(pf.relative_path.lower() in ("readme.md", "readme.rst", "readme.txt") for pf in parsed_files)
    doc_files = summary.languages.get("markdown", {}).get("files", 0)

    comment_lines = 0
    code_lines = 0
    for pf in parsed_files:
        if pf.language in ("markdown", "json", "yaml", "toml", "xml", "text", "other"):
            continue
        for line in pf.source.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            code_lines += 1
            if stripped.startswith(_COMMENT_PREFIXES):
                comment_lines += 1
    comment_ratio = comment_lines / code_lines if code_lines else 0

    score = 40 if has_readme else 10
    score += min(30, doc_files * 5)
    score += min(30, round(comment_ratio * 150))
    score = _clamp(score)

    reasoning = [
        "README present" if has_readme else "no README found",
        f"{doc_files} markdown doc file(s)",
        f"{comment_ratio:.0%} of non-blank code lines are comments",
    ]
    return {"score": score, "reasoning": reasoning}
