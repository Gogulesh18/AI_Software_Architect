"""API flow: Client -> endpoint -> handler file, grouped by detected endpoint."""

from app.diagram.common import diagram_result, edge, node


def build_api_flow_diagram(api_surface: dict) -> dict:
    nodes = [node("client", "clientNode", "Client")]
    edges = []
    file_nodes_added: set[str] = set()

    for i, ep in enumerate(api_surface.get("endpoints", [])):
        ep_id = f"endpoint::{i}"
        label = f"{ep['method']} {ep['path']}"
        nodes.append(node(ep_id, "endpointNode", label, framework=ep.get("framework")))
        edges.append(edge("client", ep_id, edge_type="request"))

        file_id = f"file::{ep['file']}"
        if file_id not in file_nodes_added:
            nodes.append(node(file_id, "fileNode", ep["file"]))
            file_nodes_added.add(file_id)
        edges.append(edge(ep_id, file_id, label=f"line {ep['line']}", edge_type="handled_by"))

    return diagram_result("api_flow", nodes, edges)
