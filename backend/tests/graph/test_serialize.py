from app.graph.builder import build_graph
from app.graph.serialize import graph_from_json, graph_to_json
from app.parser.extractor import parse_source


def test_roundtrip_preserves_nodes_and_edges():
    pf = parse_source("a.py", "python", "class Foo:\n    def bar(self):\n        pass\n")
    original = build_graph([pf])

    restored = graph_from_json(graph_to_json(original))

    assert set(restored.nodes) == set(original.nodes)
    assert restored.number_of_edges() == original.number_of_edges()
    for node_id in original.nodes:
        assert restored.nodes[node_id]["type"] == original.nodes[node_id]["type"]


def test_to_json_produces_plain_dicts_with_ids():
    pf = parse_source("a.py", "python", "def f():\n    pass\n")
    graph = build_graph([pf])

    data = graph_to_json(graph)

    assert all("id" in n for n in data["nodes"])
    assert all({"source", "target"} <= e.keys() for e in data["edges"])
