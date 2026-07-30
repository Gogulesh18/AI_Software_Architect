"""Shared helpers for building React-Flow-ready {nodes, edges} JSON.

No layout/positions are computed here — per ARCHITECTURE.md, the backend
emits plain graph data and the frontend owns rendering/auto-layout (dagre).
Every diagram caps its node count so a huge repo can't ship a payload the
browser can't render.
"""

MAX_NODES = 300


def node(node_id: str, node_type: str, label: str, **data) -> dict:
    return {"id": node_id, "type": node_type, "data": {"label": label, **data}}


def edge(source: str, target: str, label: str = "", edge_type: str = "default", **data) -> dict:
    return {
        "id": f"{source}->{target}:{label}" if label else f"{source}->{target}",
        "source": source,
        "target": target,
        "label": label,
        "type": edge_type,
        "data": data,
    }


def cap(nodes: list[dict], edges: list[dict], max_nodes: int = MAX_NODES) -> tuple[list[dict], list[dict], bool]:
    if len(nodes) <= max_nodes:
        return nodes, edges, False
    kept_ids = {n["id"] for n in nodes[:max_nodes]}
    kept_edges = [e for e in edges if e["source"] in kept_ids and e["target"] in kept_ids]
    return nodes[:max_nodes], kept_edges, True


def diagram_result(diagram_type: str, nodes: list[dict], edges: list[dict], max_nodes: int = MAX_NODES) -> dict:
    nodes, edges, truncated = cap(nodes, edges, max_nodes)
    return {"type": diagram_type, "nodes": nodes, "edges": edges, "truncated": truncated}
