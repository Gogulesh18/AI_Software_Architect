"""ER diagram from app.analyzer.database's detected tables/columns/relationships."""

from app.diagram.common import diagram_result, edge, node


def build_er_diagram(database_schema: dict) -> dict:
    nodes = [
        node(
            table["name"],
            "tableNode",
            table["name"],
            orm=table["orm"],
            file=table["file"],
            columns=table["columns"],
        )
        for table in database_schema.get("tables", [])
    ]

    edges = [
        edge(rel["from"], rel["to"], label=rel["via"], edge_type="relationship")
        for rel in database_schema.get("relationships", [])
        if rel["from"] != rel["to"]
    ]

    return diagram_result("er_diagram", nodes, edges)
