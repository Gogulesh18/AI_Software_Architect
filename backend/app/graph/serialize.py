"""Graph <-> plain-JSON conversion (storage + diagram module input)."""

import networkx as nx


def graph_to_json(graph: nx.MultiDiGraph) -> dict:
    nodes = [{"id": node_id, **attrs} for node_id, attrs in graph.nodes(data=True)]
    edges = [
        {"source": u, "target": v, **attrs}
        for u, v, attrs in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}


def graph_from_json(data: dict) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for node in data.get("nodes", []):
        node_id = node["id"]
        attrs = {k: v for k, v in node.items() if k != "id"}
        graph.add_node(node_id, **attrs)
    for edge in data.get("edges", []):
        source, target = edge["source"], edge["target"]
        attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
        graph.add_edge(source, target, **attrs)
    return graph
