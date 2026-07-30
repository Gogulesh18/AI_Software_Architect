"""Data flow diagram: Client -> (detected layers) -> Database, built from the
same folder-name signals as app.analyzer.architecture. Falls back to a
generic Client -> Application -> Database chain when no layering is found."""

from app.diagram.common import diagram_result, edge, node
from app.parser.models import ParsedFile

_LAYERS = [
    ("input", "API / Controllers", ("controllers", "controller", "routes", "route", "api", "handlers")),
    ("business", "Services / Business Logic", ("services", "service", "usecases", "use_cases", "domain")),
    ("data", "Repositories / Data Access", ("repositories", "repository", "dao", "models", "model")),
]


def build_data_flow_diagram(parsed_files: list[ParsedFile], database_schema: dict) -> dict:
    folders = {p.lower() for pf in parsed_files for p in pf.relative_path.split("/")[:-1]}

    present_layers = [(key, label) for key, label, names in _LAYERS if folders & set(names)]

    nodes = [node("client", "clientNode", "Client")]
    edges = []
    previous = "client"

    if not present_layers:
        nodes.append(node("app", "processNode", "Application"))
        edges.append(edge("client", "app"))
        previous = "app"
    else:
        for key, label in present_layers:
            nodes.append(node(key, "processNode", label))
            edges.append(edge(previous, key))
            previous = key

    if database_schema.get("tables"):
        nodes.append(node("database", "databaseNode", "Database"))
        edges.append(edge(previous, "database"))

    return diagram_result("data_flow_diagram", nodes, edges)
