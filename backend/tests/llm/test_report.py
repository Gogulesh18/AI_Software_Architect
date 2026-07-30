from app.analyzer.pipeline import run_all_analyzers
from app.graph.builder import build_graph
from app.graph.summary import compute_summary
from app.llm.report import synthesize_report
from app.parser.ecosystem import EcosystemInfo
from app.parser.extractor import parse_source


def test_report_falls_back_to_template_without_api_key():
    # This test environment has no ANTHROPIC_API_KEY set, so synthesize_report
    # must use the deterministic template path rather than erroring.
    files = [parse_source("app.py", "python", "def add(a, b):\n    return a + b\n")]
    graph = build_graph(files)
    summary = compute_summary(files, EcosystemInfo([], []))
    analysis = run_all_analyzers(files, graph, summary)

    report = synthesize_report("demo-repo", summary, analysis)

    assert "demo-repo" in report
    assert "Architecture" in report
    assert "no ANTHROPIC_API_KEY" in report
    assert "Engineering Scores" in report
