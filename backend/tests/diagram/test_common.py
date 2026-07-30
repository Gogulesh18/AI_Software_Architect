from app.diagram.common import cap, diagram_result, edge, node


def test_cap_truncates_nodes_and_drops_dangling_edges():
    nodes = [node(str(i), "fileNode", str(i)) for i in range(5)]
    edges = [edge("0", "1"), edge("3", "4")]  # second edge references a node past the cap

    kept_nodes, kept_edges, truncated = cap(nodes, edges, max_nodes=3)

    assert len(kept_nodes) == 3
    assert truncated is True
    assert kept_edges == [edge("0", "1")]


def test_cap_no_truncation_when_under_limit():
    nodes = [node("a", "fileNode", "a")]
    kept_nodes, _kept_edges, truncated = cap(nodes, [], max_nodes=10)
    assert truncated is False
    assert kept_nodes == nodes


def test_diagram_result_shape():
    result = diagram_result("test_type", [node("a", "fileNode", "a")], [])
    assert result == {"type": "test_type", "nodes": [node("a", "fileNode", "a")], "edges": [], "truncated": False}
