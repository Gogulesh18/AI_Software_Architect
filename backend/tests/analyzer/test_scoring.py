from app.analyzer.pipeline import run_all_analyzers
from app.graph.builder import build_graph
from app.graph.summary import compute_summary
from app.parser.ecosystem import EcosystemInfo
from app.parser.extractor import parse_source

_EXPECTED_KEYS = {
    "architecture", "security", "performance", "maintainability",
    "readability", "scalability", "testability", "documentation", "overall",
}


def _run(files):
    graph = build_graph(files)
    summary = compute_summary(files, EcosystemInfo([], []))
    return run_all_analyzers(files, graph, summary)


def test_clean_small_repo_scores_reasonably_well():
    files = [
        parse_source("README.md", "markdown", "# My Project\n\nA clean little app.\n"),
        parse_source("app/main.py", "python", "def add(a, b):\n    return a + b\n"),
        parse_source("tests/test_main.py", "python", "def test_add():\n    assert True\n"),
    ]
    bundle = _run(files)

    assert set(bundle.scores.keys()) == _EXPECTED_KEYS
    for entry in bundle.scores.values():
        assert 0 <= entry["score"] <= 100
        assert entry["reasoning"]

    assert bundle.scores["security"]["score"] == 100
    assert bundle.scores["overall"]["score"] > 50


def test_risky_repo_scores_worse_on_security_and_performance():
    risky_src = '''
API_KEY = "sk-1234567890abcdef"

def list_orders(users):
    for user in users:
        db.execute(f"SELECT * FROM orders WHERE user_id = {user.id}")
'''
    files = [parse_source("app.py", "python", risky_src)]
    bundle = _run(files)

    assert bundle.scores["security"]["score"] < 100
    assert bundle.scores["performance"]["score"] < 100


def test_all_bundle_fields_are_dicts():
    files = [parse_source("main.py", "python", "x = 1\n")]
    bundle = _run(files)

    for field_name in ("architecture", "database_schema", "api_surface", "patterns", "solid", "quality", "security", "performance", "scores"):
        assert isinstance(getattr(bundle, field_name), dict)
