"""Runs every analyzer over one parsed repo and bundles the results.

This is the single contract app.workers.pipeline depends on — each analyzer
module is free to change internally as long as `run_all_analyzers` keeps
returning an AnalysisBundle with these nine fields.
"""

from dataclasses import dataclass

import networkx as nx

from app.analyzer.api_surface import detect_api_surface
from app.analyzer.architecture import detect_architecture
from app.analyzer.database import detect_database
from app.analyzer.patterns import detect_patterns
from app.analyzer.performance import analyze_performance
from app.analyzer.quality import analyze_quality
from app.analyzer.scoring import compute_scores
from app.analyzer.security import analyze_security
from app.analyzer.solid import analyze_solid
from app.graph.summary import RepoSummary
from app.parser.models import ParsedFile


@dataclass(slots=True)
class AnalysisBundle:
    architecture: dict
    database_schema: dict
    api_surface: dict
    patterns: dict
    solid: dict
    quality: dict
    security: dict
    performance: dict
    scores: dict


def run_all_analyzers(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph, summary: RepoSummary) -> AnalysisBundle:
    architecture = detect_architecture(parsed_files, summary)
    database_schema = detect_database(parsed_files)
    api_surface = detect_api_surface(parsed_files)
    patterns = detect_patterns(parsed_files, graph)
    solid = analyze_solid(parsed_files, graph)
    quality = analyze_quality(parsed_files, graph)
    security = analyze_security(parsed_files)
    performance = analyze_performance(parsed_files)

    scores = compute_scores(
        parsed_files=parsed_files,
        summary=summary,
        architecture=architecture,
        quality=quality,
        security=security,
        performance=performance,
        solid=solid,
    )

    return AnalysisBundle(
        architecture=architecture,
        database_schema=database_schema,
        api_surface=api_surface,
        patterns=patterns,
        solid=solid,
        quality=quality,
        security=security,
        performance=performance,
        scores=scores,
    )
