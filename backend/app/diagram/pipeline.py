"""Builds every diagram type for one analyzed repo, keyed by diagram type name."""

import networkx as nx

from app.analyzer.pipeline import AnalysisBundle
from app.diagram.api_flow import build_api_flow_diagram
from app.diagram.architecture_diagram import build_architecture_diagram, build_component_diagram
from app.diagram.call_graph import build_call_graph_diagram
from app.diagram.class_diagram import build_class_diagram
from app.diagram.data_flow import build_data_flow_diagram
from app.diagram.deployment import build_deployment_diagram
from app.diagram.er_diagram import build_er_diagram
from app.diagram.folder_tree import build_folder_tree_diagram
from app.diagram.module_graph import (
    build_module_dependency_diagram,
    build_package_dependency_diagram,
)
from app.diagram.sequence import build_sequence_diagram
from app.graph.summary import RepoSummary
from app.parser.models import ParsedFile


def build_all_diagrams(
    parsed_files: list[ParsedFile], graph: nx.MultiDiGraph, summary: RepoSummary, analysis: AnalysisBundle
) -> dict:
    diagrams = {
        "folder_tree": build_folder_tree_diagram(summary.folder_tree),
        "module_dependency": build_module_dependency_diagram(graph),
        "package_dependency": build_package_dependency_diagram(graph),
        "call_graph": build_call_graph_diagram(graph),
        "class_diagram": build_class_diagram(graph),
        "architecture_diagram": build_architecture_diagram(graph),
        "component_diagram": build_component_diagram(graph),
        "er_diagram": build_er_diagram(analysis.database_schema),
        "api_flow": build_api_flow_diagram(analysis.api_surface),
        "deployment_diagram": build_deployment_diagram(parsed_files, analysis.database_schema, analysis.api_surface),
        "sequence_diagram": build_sequence_diagram(parsed_files, graph, analysis.api_surface),
        "data_flow_diagram": build_data_flow_diagram(parsed_files, analysis.database_schema),
    }
    return diagrams
