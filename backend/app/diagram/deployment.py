"""Deployment diagram: parsed from docker-compose.yml services/depends_on
when present (simple line-based reader, not a full YAML parser — handles
the conventional 2-space-indent style docker-compose files actually use),
falling back to a generic Client -> App -> Database chain otherwise."""

from app.diagram.common import diagram_result, edge, node
from app.parser.models import ParsedFile

_COMPOSE_NAMES = {"docker-compose.yml", "docker-compose.yaml"}


def build_deployment_diagram(parsed_files: list[ParsedFile], database_schema: dict, api_surface: dict) -> dict:
    compose_file = next((pf for pf in parsed_files if pf.relative_path.rsplit("/", 1)[-1] in _COMPOSE_NAMES), None)
    if compose_file is not None:
        services = _parse_compose_services(compose_file.source)
        if services:
            return _diagram_from_services(services)
    return _fallback_diagram(database_schema, api_surface)


def _parse_compose_services(source: str) -> dict[str, dict]:
    services: dict[str, dict] = {}
    in_services = False
    current: str | None = None
    in_depends_on = False

    for raw_line in source.splitlines():
        if not raw_line.strip():
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line.strip()

        if indent == 0:
            in_services = content == "services:"
            current = None
            continue
        if not in_services:
            continue

        if indent == 2 and content.endswith(":"):
            current = content[:-1].strip("\"'")
            services[current] = {"depends_on": [], "image": None}
            in_depends_on = False
            continue
        if current is None:
            continue

        if content.startswith("depends_on:"):
            in_depends_on = True
            rest = content[len("depends_on:") :].strip()
            if rest.startswith("["):
                services[current]["depends_on"] += [x.strip().strip("\"'") for x in rest.strip("[]").split(",") if x.strip()]
                in_depends_on = False
            continue

        if in_depends_on:
            if content.startswith("- "):
                services[current]["depends_on"].append(content[2:].strip().strip("\"'"))
                continue
            if indent >= 6 and content.endswith(":"):
                services[current]["depends_on"].append(content[:-1].strip("\"'"))
                continue
            in_depends_on = False

        if content.startswith("image:"):
            services[current]["image"] = content[len("image:") :].strip().strip("\"'")

    return services


def _diagram_from_services(services: dict[str, dict]) -> dict:
    nodes = [node(name, "serviceNode", name, image=info.get("image")) for name, info in services.items()]
    edges = [
        edge(name, dep, edge_type="depends_on")
        for name, info in services.items()
        for dep in info["depends_on"]
        if dep in services
    ]
    return diagram_result("deployment_diagram", nodes, edges)


def _fallback_diagram(database_schema: dict, api_surface: dict) -> dict:
    nodes = [node("client", "clientNode", "Client"), node("app", "serviceNode", "Application")]
    edges = [edge("client", "app", label="requests" if api_surface.get("endpoints") else "")]

    if database_schema.get("tables"):
        nodes.append(node("database", "databaseNode", "Database", orms=database_schema.get("orms_detected", [])))
        edges.append(edge("app", "database", label="reads/writes"))

    return diagram_result("deployment_diagram", nodes, edges)
