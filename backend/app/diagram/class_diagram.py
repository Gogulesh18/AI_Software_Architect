"""Class diagram: class nodes carrying their method list as data, inherits edges."""

import networkx as nx

from app.diagram.common import diagram_result, edge, node


def build_class_diagram(graph: nx.MultiDiGraph) -> dict:
    nodes = []
    edges = []

    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("type") != "class":
            continue
        methods = [
            graph.nodes[m]["name"]
            for _, m, e_attrs in graph.out_edges(node_id, data=True)
            if e_attrs.get("type") == "defines" and graph.nodes[m].get("type") == "method"
        ]
        nodes.append(
            node(
                node_id,
                "classNode",
                attrs.get("name", node_id),
                file=attrs.get("file"),
                methods=sorted(methods),
                base_classes=attrs.get("base_classes", []),
            )
        )

    for u, v, attrs in graph.edges(data=True):
        if attrs.get("type") == "inherits":
            edges.append(edge(u, v, label="inherits", edge_type="inherits"))

    return diagram_result("class_diagram", nodes, edges)
