"""Function/method call graph — resolved `calls` edges only (see app.graph.builder)."""

import networkx as nx

from app.diagram.common import diagram_result, edge, node


def build_call_graph_diagram(graph: nx.MultiDiGraph) -> dict:
    call_edges = [(u, v) for u, v, attrs in graph.edges(data=True) if attrs.get("type") == "calls"]
    involved = {n for pair in call_edges for n in pair}

    nodes = []
    for node_id in involved:
        attrs = graph.nodes[node_id]
        nodes.append(
            node(
                node_id,
                "functionNode",
                attrs.get("name", node_id),
                file=attrs.get("file"),
                parent_class=attrs.get("parent_class"),
                complexity=attrs.get("complexity"),
            )
        )

    edges = [edge(u, v, edge_type="calls") for u, v in call_edges]
    return diagram_result("call_graph", nodes, edges)
