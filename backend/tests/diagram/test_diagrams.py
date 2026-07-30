from app.analyzer.pipeline import run_all_analyzers
from app.diagram.pipeline import build_all_diagrams
from app.graph.builder import build_graph
from app.graph.summary import compute_summary
from app.parser.ecosystem import EcosystemInfo
from app.parser.extractor import parse_source


def _build_sample():
    files = [
        parse_source(
            "app/controllers/user_controller.py",
            "python",
            '@app.get("/users")\ndef list_users():\n    return UserRepository().find_all()\n',
        ),
        parse_source(
            "app/repositories/user_repository.py",
            "python",
            'class UserRepository(Base):\n    __tablename__ = "users"\n    id = Column(Integer, primary_key=True)\n\n    def find_all(self):\n        return []\n',
        ),
        parse_source("docker-compose.yml", "yaml", "services:\n  backend:\n    image: app:latest\n    depends_on:\n      - db\n  db:\n    image: postgres:16\n"),
    ]
    graph = build_graph(files)
    summary = compute_summary(files, EcosystemInfo([], []))
    analysis = run_all_analyzers(files, graph, summary)
    return files, graph, summary, analysis


def test_all_diagram_types_present_with_valid_shape():
    files, graph, summary, analysis = _build_sample()
    diagrams = build_all_diagrams(files, graph, summary, analysis)

    expected_types = {
        "folder_tree", "module_dependency", "package_dependency", "call_graph",
        "class_diagram", "architecture_diagram", "component_diagram", "er_diagram",
        "api_flow", "deployment_diagram", "sequence_diagram", "data_flow_diagram",
    }
    assert set(diagrams.keys()) == expected_types

    for diagram_type, diagram in diagrams.items():
        assert diagram["type"] == diagram_type
        node_ids = {n["id"] for n in diagram["nodes"]}
        assert len(node_ids) == len(diagram["nodes"]), f"{diagram_type} has duplicate node ids"
        for e in diagram["edges"]:
            assert e["source"] in node_ids, f"{diagram_type} edge source not in nodes"
            assert e["target"] in node_ids, f"{diagram_type} edge target not in nodes"


def test_er_diagram_has_users_table():
    _, _, _, analysis = _build_sample()
    from app.diagram.er_diagram import build_er_diagram

    diagram = build_er_diagram(analysis.database_schema)
    table_names = {n["id"] for n in diagram["nodes"]}
    assert "users" in table_names


def test_api_flow_has_client_and_endpoint():
    _, _, _, analysis = _build_sample()
    from app.diagram.api_flow import build_api_flow_diagram

    diagram = build_api_flow_diagram(analysis.api_surface)
    labels = {n["data"]["label"] for n in diagram["nodes"]}
    assert "Client" in labels
    assert any("GET /users" in label for label in labels)


def test_deployment_diagram_parses_compose_services():
    files, _, _, _ = _build_sample()
    from app.diagram.deployment import build_deployment_diagram

    diagram = build_deployment_diagram(files, {}, {})
    node_ids = {n["id"] for n in diagram["nodes"]}
    assert node_ids == {"backend", "db"}
    edge_pairs = {(e["source"], e["target"]) for e in diagram["edges"]}
    assert ("backend", "db") in edge_pairs


def test_deployment_fallback_without_compose():
    from app.diagram.deployment import build_deployment_diagram

    diagram = build_deployment_diagram([], {"tables": [{"name": "x"}]}, {"endpoints": [{}]})
    node_ids = {n["id"] for n in diagram["nodes"]}
    assert node_ids == {"client", "app", "database"}


def test_data_flow_diagram_detects_layers():
    files, _, _, analysis = _build_sample()
    from app.diagram.data_flow import build_data_flow_diagram

    diagram = build_data_flow_diagram(files, analysis.database_schema)
    node_ids = {n["id"] for n in diagram["nodes"]}
    assert "input" in node_ids  # controllers/ folder
    assert "data" in node_ids  # repositories/ folder
    assert "database" in node_ids


def test_folder_tree_diagram_matches_summary():
    _files, _graph, summary, _analysis = _build_sample()
    from app.diagram.folder_tree import build_folder_tree_diagram

    diagram = build_folder_tree_diagram(summary.folder_tree)
    assert diagram["nodes"]
    file_paths = {n["id"] for n in diagram["nodes"] if n["type"] == "fileNode"}
    assert "app/controllers/user_controller.py" in file_paths


def test_class_diagram_includes_methods():
    _, graph, _, _ = _build_sample()
    from app.diagram.class_diagram import build_class_diagram

    diagram = build_class_diagram(graph)
    repo_node = next(n for n in diagram["nodes"] if n["data"]["label"] == "UserRepository")
    assert "find_all" in repo_node["data"]["methods"]


def test_empty_repo_produces_empty_but_valid_diagrams():
    graph = build_graph([])
    summary = compute_summary([], EcosystemInfo([], []))
    from app.analyzer.pipeline import run_all_analyzers as run

    analysis = run([], graph, summary)
    diagrams = build_all_diagrams([], graph, summary, analysis)
    for diagram in diagrams.values():
        assert isinstance(diagram["nodes"], list)
        assert isinstance(diagram["edges"], list)
