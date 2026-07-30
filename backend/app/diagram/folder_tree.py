"""Folder tree -> React Flow nodes/edges (parent-child, dir + file nodes)."""

from app.diagram.common import diagram_result, edge, node


def build_folder_tree_diagram(folder_tree: dict) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []

    def walk(entry: dict, parent_id: str | None) -> None:
        node_id = entry["path"] or "/"
        if entry["type"] == "dir":
            nodes.append(
                node(node_id, "folderNode", entry["name"] or "/", file_count=entry.get("file_count"), primary_language=entry.get("primary_language"))
            )
            if parent_id is not None:
                edges.append(edge(parent_id, node_id))
            for child in entry.get("children", []):
                walk(child, node_id)
        else:
            nodes.append(node(node_id, "fileNode", entry["name"], language=entry.get("language"), loc=entry.get("loc")))
            if parent_id is not None:
                edges.append(edge(parent_id, node_id))

    walk(folder_tree, None)
    return diagram_result("folder_tree", nodes, edges)
