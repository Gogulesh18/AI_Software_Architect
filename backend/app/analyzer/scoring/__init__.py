"""Aggregates analyzer findings into architecture/scalability/maintainability/etc. scores."""

from app.analyzer.scoring.detector import compute_scores

__all__ = ["compute_scores"]
