import json

import pytest

from app.database.models import AnalysisResult
from app.export.service import UnsupportedExportFormatError, export_result


def _result() -> AnalysisResult:
    return AnalysisResult(
        job_id="job-1",
        summary={"total_files": 3},
        architecture={"primary_style": "Monolith", "confidence": 60, "evidence": []},
        folders={},
        dependency_graph={"nodes": [], "edges": []},
        database_schema={"orms_detected": [], "tables": [], "relationships": []},
        api_surface={"protocols": [], "endpoints": [], "endpoint_count": 0, "auth": {"detected": False, "mechanisms": []}},
        patterns={"summary": {}, "matches": []},
        solid={"summary": {}, "violations": []},
        quality={"metrics": {}, "findings": []},
        security={"summary": {}, "findings": []},
        performance={"summary": {}, "findings": []},
        scores={"overall": {"score": 80, "reasoning": ["clean repo"]}},
        diagrams={},
        report_markdown="# Report\n\n## Summary\n- point one—with an em dash\n- “quoted” point two\n\n```\ncode block\n```\n",
    )


def test_markdown_export():
    content, media_type, filename = export_result("My Repo", _result(), "markdown")
    assert media_type == "text/markdown"
    assert filename == "My_Repo-report.md"
    assert b"# Report" in content


def test_json_export_round_trips():
    content, media_type, _filename = export_result("My Repo", _result(), "json")
    assert media_type == "application/json"
    data = json.loads(content)
    assert data["scores"]["overall"]["score"] == 80


def test_pdf_export_produces_nonempty_pdf_bytes():
    content, media_type, filename = export_result("My Repo", _result(), "pdf")
    assert media_type == "application/pdf"
    assert filename == "My_Repo-report.pdf"
    assert content.startswith(b"%PDF")
    assert len(content) > 500


def test_unsupported_format_raises():
    with pytest.raises(UnsupportedExportFormatError):
        export_result("My Repo", _result(), "docx")
