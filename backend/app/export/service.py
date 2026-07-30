"""Report export: Markdown (raw), JSON (full result bundle), PDF (rendered
from the same Markdown report — a minimal heading/bullet/code-fence
renderer, not a full CommonMark implementation, which is all a generated
architecture report actually needs)."""

import json
import re

from fpdf import FPDF

from app.core.exceptions import AppError
from app.database.models import AnalysisResult


class UnsupportedExportFormatError(AppError):
    status_code = 400


def export_result(repo_name: str, result: AnalysisResult, fmt: str) -> tuple[bytes, str, str]:
    safe_name = re.sub(r"[^\w.-]", "_", repo_name)

    if fmt == "markdown":
        return (result.report_markdown or "").encode("utf-8"), "text/markdown", f"{safe_name}-report.md"

    if fmt == "json":
        payload = {
            "summary": result.summary,
            "architecture": result.architecture,
            "folders": result.folders,
            "dependency_graph": result.dependency_graph,
            "database_schema": result.database_schema,
            "api_surface": result.api_surface,
            "patterns": result.patterns,
            "solid": result.solid,
            "quality": result.quality,
            "security": result.security,
            "performance": result.performance,
            "scores": result.scores,
            "diagrams": result.diagrams,
            "report_markdown": result.report_markdown,
        }
        return json.dumps(payload, indent=2, default=str).encode("utf-8"), "application/json", f"{safe_name}-report.json"

    if fmt == "pdf":
        return _render_pdf(repo_name, result.report_markdown or ""), "application/pdf", f"{safe_name}-report.pdf"

    raise UnsupportedExportFormatError(f"Unsupported export format: {fmt!r} (use markdown, json, or pdf)")


# fpdf2's core fonts (Helvetica/Courier) are latin-1 only. LLM-generated
# markdown routinely contains smart quotes/em-dashes/bullets that aren't in
# latin-1 — transliterate the common ones and replace anything else rather
# than crashing PDF export (which would otherwise need a bundled Unicode
# TTF font just to render an em-dash).
_UNICODE_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "•": "-", "…": "...",
}


def _latin1_safe(text: str) -> str:
    for uni, ascii_eq in _UNICODE_REPLACEMENTS.items():
        text = text.replace(uni, ascii_eq)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _line(pdf: FPDF, height: float, text: str) -> None:
    # multi_cell's default new_x=XPos.RIGHT leaves the cursor near the right
    # margin after rendering — fine for "more content on this line" use
    # cases, wrong for a document renderer where every call is its own line.
    # Without new_x="LMARGIN" here, two non-blank markdown lines in a row
    # (no blank line between them, e.g. a heading immediately followed by a
    # bullet) leave the next call almost no horizontal space to render into
    # and fpdf2 raises FPDFException("Not enough horizontal space...").
    pdf.multi_cell(0, height, text, new_x="LMARGIN", new_y="NEXT")


def _render_pdf(repo_name: str, markdown: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    _line(pdf, 10, _latin1_safe(f"Architecture Report: {repo_name}"))
    pdf.ln(4)

    in_code_block = False
    for line in markdown.splitlines():
        line = _latin1_safe(line)
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            pdf.set_font("Courier", "", 9)
            _line(pdf, 5, line or " ")
            continue

        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            _line(pdf, 9, line[2:])
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            _line(pdf, 8, line[3:])
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            _line(pdf, 7, line[4:])
        elif line.strip().startswith(("- ", "* ")):
            pdf.set_font("Helvetica", "", 10)
            _line(pdf, 6, f"  - {line.strip()[2:]}")
        elif line.strip():
            pdf.set_font("Helvetica", "", 10)
            _line(pdf, 6, line)
        else:
            pdf.ln(2)

    return bytes(pdf.output())
