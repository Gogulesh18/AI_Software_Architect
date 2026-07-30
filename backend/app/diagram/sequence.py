"""Best-effort sequence diagrams for the first few detected API endpoints:
Client -> handler -> resolved calls, breadth-first up to a small depth.
Only as good as the call-graph resolution in app.graph.builder (ambiguous
calls are left unlinked there, so a flow may legitimately stop early)."""

import networkx as nx

from app.diagram.common import diagram_result, edge, node
from app.graph.builder import symbol_id
from app.parser.models import ParsedFile

MAX_FLOWS = 3
MAX_DEPTH = 4


def build_sequence_diagram(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph, api_surface: dict) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    by_path: dict[str, ParsedFile] = {pf.relative_path: pf for pf in parsed_files}

    for flow_idx, ep in enumerate(api_surface.get("endpoints", [])[:MAX_FLOWS]):
        handler = _find_handler_symbol(by_path.get(ep["file"]), ep["line"])
        if handler is None:
            continue

        prefix = f"seq{flow_idx}::"
        client_id = f"{prefix}client"
        nodes.append(node(client_id, "participantNode", "Client", flow=flow_idx))

        start_id = f"{prefix}{symbol_id(ep['file'], handler.name, handler.parent_class)}"
        nodes.append(node(start_id, "participantNode", f"{ep['method']} {ep['path']} → {handler.name}", flow=flow_idx))
        edges.append(edge(client_id, start_id, label="1", edge_type="call"))

        graph_node_id = symbol_id(ep["file"], handler.name, handler.parent_class)
        _walk_calls(graph, graph_node_id, prefix, flow_idx, nodes, edges, start_id, step=2, depth=0, visited={graph_node_id})

    return diagram_result("sequence_diagram", nodes, edges)


def _find_handler_symbol(pf: ParsedFile | None, line: int):
    if pf is None:
        return None
    candidates = [s for s in pf.functions if s.start_line <= line <= s.end_line + 5]
    if not candidates:
        # decorator line sits just above the function; widen the search
        candidates = [s for s in pf.functions if abs(s.start_line - line) <= 3]
    return min(candidates, key=lambda s: abs(s.start_line - line), default=None)


def _walk_calls(graph, current_graph_id, prefix, flow_idx, nodes, edges, current_diagram_id, step, depth, visited):
    if depth >= MAX_DEPTH or not graph.has_node(current_graph_id):
        return
    for _, target, attrs in graph.out_edges(current_graph_id, data=True):
        if attrs.get("type") != "calls" or target in visited:
            continue
        visited.add(target)
        target_attrs = graph.nodes[target]
        target_diagram_id = f"{prefix}{target}"
        nodes.append(node(target_diagram_id, "participantNode", target_attrs.get("name", target), flow=flow_idx))
        edges.append(edge(current_diagram_id, target_diagram_id, label=str(step), edge_type="call"))
        _walk_calls(graph, target, prefix, flow_idx, nodes, edges, target_diagram_id, step + 1, depth + 1, visited)
