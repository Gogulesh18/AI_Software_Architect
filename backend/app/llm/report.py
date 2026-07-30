"""Executive report synthesis. All *findings* come from the deterministic
Phase 3 analyzers — the LLM only writes narrative prose around numbers that
are already computed, per ARCHITECTURE.md's "rule-based first, LLM second"
design. Falls back to a template-rendered report (no prose, just the facts)
when no LLM is configured, so a report always exists."""

from app.analyzer.pipeline import AnalysisBundle
from app.graph.summary import RepoSummary
from app.llm import get_llm_provider

_SYSTEM_PROMPT = """You are a principal software architect writing an executive architecture \
report for another engineer. Be precise and specific, cite file paths where the input data \
includes them, and do not invent facts beyond what's given. Write in Markdown with clear \
section headers matching: Project Summary, Tech Stack, Architecture, Folder Structure, \
Database, API, Design Patterns, SOLID Analysis, Security, Performance, Scalability, \
Strengths, Weaknesses, Recommendations, Future Improvements."""


def synthesize_report(repo_name: str, summary: RepoSummary, analysis: AnalysisBundle) -> str:
    llm = get_llm_provider()
    facts = _build_facts(repo_name, summary, analysis)

    if not llm.is_available:
        return _template_report(repo_name, summary, analysis)

    user_prompt = (
        "Write the executive architecture report described in your instructions, using only "
        f"the facts below.\n\n{facts}"
    )
    try:
        return llm.complete(_SYSTEM_PROMPT, user_prompt, max_tokens=4000)
    except Exception as exc:  # noqa: BLE001 - provider failures are unpredictable by nature and shouldn't fail the whole job
        return _template_report(repo_name, summary, analysis) + f"\n\n> _LLM report generation failed ({exc}); showing the template report instead._\n"


def _build_facts(repo_name: str, summary: RepoSummary, analysis: AnalysisBundle) -> str:
    lang_lines = "\n".join(f"- {lang}: {stats['files']} files, {stats['loc']} LOC" for lang, stats in summary.languages.items())
    scores_lines = "\n".join(f"- {name}: {entry['score']}/100 ({'; '.join(entry['reasoning'])})" for name, entry in analysis.scores.items())

    return f"""
Repository: {repo_name}
Total files: {summary.total_files}, total LOC: {summary.total_loc}
Primary language: {summary.primary_language}
Frameworks detected: {', '.join(summary.frameworks) or 'none detected'}

Languages:
{lang_lines}

Architecture style: {analysis.architecture['primary_style']} (confidence {analysis.architecture['confidence']}%)
Evidence: {'; '.join(analysis.architecture['evidence'])}

Database: {', '.join(analysis.database_schema['orms_detected']) or 'none detected'}, {len(analysis.database_schema['tables'])} table(s)
API: protocols={', '.join(analysis.api_surface['protocols']) or 'none'}, {analysis.api_surface['endpoint_count']} endpoint(s), auth={analysis.api_surface['auth']}

Design patterns detected: {analysis.patterns['summary']}
SOLID violations: {analysis.solid['summary']}
Quality findings: {len(analysis.quality['findings'])} (metrics: {analysis.quality['metrics']})
Security findings: {analysis.security['summary']}
Performance findings: {analysis.performance['summary']}

Engineering scores:
{scores_lines}
""".strip()


def _template_report(repo_name: str, summary: RepoSummary, analysis: AnalysisBundle) -> str:
    scores = analysis.scores
    lines = [
        f"# Architecture Report: {repo_name}",
        "",
        "> Generated without an LLM (no ANTHROPIC_API_KEY configured) — facts only, no narrative prose.",
        "",
        "## Project Summary",
        f"- {summary.total_files} files, {summary.total_loc} lines of code",
        f"- Primary language: {summary.primary_language or 'unknown'}",
        f"- Frameworks: {', '.join(summary.frameworks) or 'none detected'}",
        "",
        "## Architecture",
        f"- Style: **{analysis.architecture['primary_style']}** (confidence {analysis.architecture['confidence']}%)",
        *[f"  - {e}" for e in analysis.architecture["evidence"]],
        "",
        "## Database",
        f"- ORMs: {', '.join(analysis.database_schema['orms_detected']) or 'none detected'}",
        f"- Tables: {len(analysis.database_schema['tables'])}",
        "",
        "## API",
        f"- Protocols: {', '.join(analysis.api_surface['protocols']) or 'none detected'}",
        f"- Endpoints: {analysis.api_surface['endpoint_count']}",
        f"- Auth: {'detected (' + ', '.join(analysis.api_surface['auth']['mechanisms']) + ')' if analysis.api_surface['auth']['detected'] else 'not detected'}",
        "",
        "## Design Patterns",
        *([f"- {pattern}: {count}" for pattern, count in analysis.patterns["summary"].items()] or ["- none detected"]),
        "",
        "## SOLID Analysis",
        *([f"- {principle}: {count} violation(s)" for principle, count in analysis.solid["summary"].items()] or ["- no violations detected"]),
        "",
        "## Security",
        *([f"- {cat}: {count}" for cat, count in analysis.security["summary"].items()] or ["- no findings"]),
        "",
        "## Performance",
        *([f"- {cat}: {count}" for cat, count in analysis.performance["summary"].items()] or ["- no findings"]),
        "",
        "## Engineering Scores",
        *[f"- {name.title()}: {entry['score']}/100 — {'; '.join(entry['reasoning'])}" for name, entry in scores.items()],
    ]
    return "\n".join(lines)
