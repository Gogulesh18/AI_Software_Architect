"""Module dependency graph (file -> file / file -> external package) and a
separate, coarser package-dependency view (Application -> external package,
weighted by how many files import it)."""

import networkx as nx

from app.diagram.common import diagram_result, edge, node


def build_module_dependency_diagram(graph: nx.MultiDiGraph) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_edges: set[tuple[str, str]] = set()

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") == "file":
            nodes.append(node(node_id, "fileNode", node_id.rsplit("/", 1)[-1], path=node_id, language=attrs.get("language")))
        elif attrs.get("type") == "external_package":
            nodes.append(node(node_id, "packageNode", attrs.get("name", node_id)))

    for u, v, attrs in graph.edges(data=True):
        if attrs.get("type") != "imports":
            continue
        if (u, v) in seen_edges:
            continue
        seen_edges.add((u, v))
        edges.append(edge(u, v, edge_type="imports"))

    return diagram_result("module_dependency", nodes, edges)


def build_package_dependency_diagram(graph: nx.MultiDiGraph, app_name: str = "Application") -> dict:
    nodes = [node("app", "appNode", app_name)]
    edges = []

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") != "external_package":
            continue
        importer_count = sum(
            1 for u, _, e_attrs in graph.in_edges(node_id, data=True) if e_attrs.get("type") == "imports"
        )
        nodes.append(node(node_id, "packageNode", attrs.get("name", node_id), importer_count=importer_count))
        edges.append(edge("app", node_id, label=f"{importer_count} file(s)"))

    return diagram_result("package_dependency", nodes, edges)
