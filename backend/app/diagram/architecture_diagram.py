"""System architecture / component diagrams: folder-level aggregation of the
file-level import graph. A raw per-file dependency graph is too dense to
read as "the architecture" — grouping by folder (component) and summing the
underlying file-to-file edges into a weighted component-to-component edge
is what actually reads as a system diagram.

`build_architecture_diagram` aggregates at top-level-folder granularity
("the system"); `build_component_diagram` goes one folder level deeper
("zoom in" on one area) — same aggregation, different depth.
"""

import networkx as nx

from app.diagram.common import diagram_result, edge, node


def _component_of(file_path: str, depth: int) -> str:
    parts = file_path.split("/")[:-1]  # drop filename
    if not parts:
        return "(root)"
    return "/".join(parts[:depth]) or "(root)"


def _build(graph: nx.MultiDiGraph, depth: int, diagram_type: str) -> dict:
    file_counts: dict[str, int] = {}
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") == "file":
            component = _component_of(node_id, depth)
            file_counts[component] = file_counts.get(component, 0) + 1

    weights: dict[tuple[str, str], int] = {}
    for u, v, attrs in graph.edges(data=True):
        if attrs.get("type") != "imports":
            continue
        if graph.nodes.get(u, {}).get("type") != "file" or graph.nodes.get(v, {}).get("type") != "file":
            continue
        cu, cv = _component_of(u, depth), _component_of(v, depth)
        if cu == cv:
            continue
        weights[(cu, cv)] = weights.get((cu, cv), 0) + 1

    nodes = [node(name, "componentNode", name, file_count=count) for name, count in file_counts.items()]
    edges = [edge(u, v, label=str(w), edge_type="depends_on", weight=w) for (u, v), w in weights.items()]
    return diagram_result(diagram_type, nodes, edges)


def build_architecture_diagram(graph: nx.MultiDiGraph) -> dict:
    return _build(graph, depth=1, diagram_type="architecture_diagram")


def build_component_diagram(graph: nx.MultiDiGraph) -> dict:
    return _build(graph, depth=2, diagram_type="component_diagram")
